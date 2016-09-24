#!/usr/bin/perl -w
#web interface to a mysql server
use strict;
use CGI;
use DBI;
use DBD::mysql;
my %form;	#this user's data
my $error;	#error flag;
if(&getData()){	#get the data from the last page's form
	if($form{'key'}){
		if(&readKey($form{'key'})){	#read the server side cookie for state
			if($form{'action'} eq "connect"){	#show login result
				if(&testConnect($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'})){	#mysql login detail are correct
					&updateKey($form{'key'});
				}
			}
			elsif($form{'action'} eq "mainmenu"){}	#just display a template
			elsif($form{'action'} eq "logout"){&deleteKey($form{'key'});}	#remove the server side cookie
			elsif($form{'action'} eq "query"){	#pick what type of query to run
				&updateKey($form{'key'});
			}
			elsif($form{'action'} eq "choosetable"){	#pick what table to run the query type on
				if(my @tables = &getTables($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'})){
					$form{'tablelist'} = "";
					for(my $tCount = 0; $tCount <= $#tables; $tCount++){$form{'tablelist'} .= "<tr><th><input type=\"checkbox\" name=\"table$tCount\" value=\"$tables[$tCount]\"></th><td>$tables[$tCount]</td></tr>\n";}	#convert to html format
					&updateKey($form{'key'});
				}
			}
			elsif($form{'action'} eq "choosefields"){	#pick what fields to use in the query
				my @tablesTemp;
				foreach my $name (keys %form){
					if($name =~ m/^table\d+$/){push(@tablesTemp, $form{$name});}
				}
				if($#tablesTemp > -1){	#one or more tables have been selected
					$form{'tables'} = join(", ", @tablesTemp);	#for the server side cookie
					if(my @fields = &getFields($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'}, $form{'tables'})){
						$form{'fieldlist'} = "";
						for(my $count = 0; $count <= $#fields; $count++){$form{'fieldlist'} .= "<tr><th><input type=\"checkbox\" name=\"field" . ($count + 1) . "\" value=\"$fields[$count]\"></th><td>$fields[$count]</td></tr>\n";}	#convert to html format
						&updateKey($form{'key'});
					}
				}
				else{$error = "You did not select any tables to query";}
			}
			elsif($form{'action'} eq "choosecriteria"){	#pick the criteria for the query
				if(my @fields = &getFields($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'}, $form{'tables'})){
					if($form{'tables'} =~ m/, /){	#more than one table selected, show the join options
						my @tables = split(/, /, $form{'tables'});
						$form{'joinlist'} = "<p>Please select how you want to join the tables to $tables[0]</p>\n";
						$form{'joinlist'} .= "<table border=\"1\" align=\"center\" bgcolor=\"#8899DD\">\n";
						for(my $tCount = 1; $tCount <= $#tables; $tCount++){
							$form{'joinlist'} .= "<tr>\n";
							$form{'joinlist'} .= "<td>left join $tables[$tCount] on</td>\n";
							$form{'joinlist'} .= "<td>\n";
							$form{'joinlist'} .= "<select name=\"joinfield1_$tables[$tCount]\">\n";
							foreach(@fields){
								if($_ !~ m/\*$/){	#ignore these fields
									$form{'joinlist'} .= "<option value=\"$_\">$_</option>";
								}
							}
							$form{'joinlist'} .= "</select>\n";
							$form{'joinlist'} .= "</td>\n";
							$form{'joinlist'} .= "<td>=</td>\n";
							$form{'joinlist'} .= "<td>\n";
							$form{'joinlist'} .= "<select name=\"joinfield2_$tables[$tCount]\">\n";
							foreach(@fields){
								if($_ !~ m/\*$/){	#ignore these fields
									$form{'joinlist'} .= "<option value=\"$_\">$_</option>";
								}
							}
							$form{'joinlist'} .= "</select>\n";
							$form{'joinlist'} .= "</td>\n";
							$form{'joinlist'} .= "</tr>\n";
						}
						$form{'joinlist'} .= "</table>\n";
					}
					else{$form{'joinlist'} = "";}	#join not used for just one table
					$form{'criterialist'} = "";
					for(my $count = 0; $count <= 5; $count++){
						$form{'criterialist'} .= "<tr>";
						$form{'criterialist'} .= "<td><select name=\"critname$count\"><option value=\"\"></option>";
						foreach(@fields){
							if($_ !~ m/\*$/){	#ignore these fields
								$form{'criterialist'} .= "<option value=\"$_\">$_</option>";
							}
						}
						$form{'criterialist'} .= "</select></td>";
						$form{'criterialist'} .= "<td><select name=\"crithow$count\">";
						foreach("=", ">=", "<=", ">", "<", "!=", "LIKE", "REGEXP"){$form{'criterialist'} .= "<option value=\"$_\">$_</option>";}
						$form{'criterialist'} .= "</select></td>";
						$form{'criterialist'} .= "<td><input type=\"text\" name=\"crit$count\"></td>";
						if($count < 5){$form{'criterialist'} .= "<td><select name=\"critappend$count\"><option value=\"AND\">AND</option><option value=\"OR\">OR</option></select></td>";}
						else{$form{'criterialist'} .= "<td>&nbsp;</td>";}
						$form{'criterialist'} .= "</tr>\n";
					}
					$form{'orderbylist'} = "";
					foreach(@fields){
						if($_ !~ m/\*$/){	#ignore these fields
							$form{'orderbylist'} .= "<option value=\"$_\">$_</option>\n";
						}
					}
					$form{'fields'} = join(", ", @fields);	#for the server side cookie
					&updateKey($form{'key'});
				}
			}
			elsif($form{'action'} eq "runquery"){	#run the query
				$form{'sql'} = &composeSelect();
				$form{'queryrecords'} = &runQuery($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'}, $form{'sql'});
			}
			elsif($form{'action'} eq "managetables"){	#show table list
				if(my @tables = &getTables($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'})){
					$form{'tablelist'} = "";
					foreach(@tables){	#convert to html format
						$form{'tablelist'} .= "<tr>\n";
						$form{'tablelist'} .= "<td>$_</td>\n";
						$form{'tablelist'} .= "<th>\n";
						$form{'tablelist'} .= "<form action=\"$ENV{'SCRIPT_NAME'}\" method=\"POST\" target=\"_blank\">\n";
						$form{'tablelist'} .= "<input type=\"hidden\" name=\"key\" value=\"$form{'key'}\">\n";
						$form{'tablelist'} .= "<input type=\"hidden\" name=\"tables\" value=\"$_\">\n";
						$form{'tablelist'} .= "<input type=\"hidden\" name=\"action\" value=\"describe\">\n";
						$form{'tablelist'} .= "<input type=\"submit\" value=\"Describe\">\n";
						$form{'tablelist'} .= "</form>\n";
						$form{'tablelist'} .= "</th>\n";
						$form{'tablelist'} .= "<th>\n";
						$form{'tablelist'} .= "<form action=\"$ENV{'SCRIPT_NAME'}\" method=\"POST\">\n";
						$form{'tablelist'} .= "<input type=\"hidden\" name=\"key\" value=\"$form{'key'}\">\n";
						$form{'tablelist'} .= "<input type=\"hidden\" name=\"tables\" value=\"$_\">\n";
						$form{'tablelist'} .= "<input type=\"hidden\" name=\"action\" value=\"droptable\">\n";
						$form{'tablelist'} .= "<input type=\"submit\" value=\"Drop\">\n";
						$form{'tablelist'} .= "</form>\n";
						$form{'tablelist'} .= "</th>\n";
						$form{'tablelist'} .= "</tr>\n";
					}
					delete $form{'tables'};
					&updateKey($form{'key'});
				}
			}
			elsif($form{'action'} eq "describe"){	#display table list
				if($form{'tables'} =~ m/^(\w+)$/){	#safety check on table name
					$form{'queryrecords'} = &runQuery($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'}, "DESCRIBE $1;");
				}
				else{$error = "Table name contains invalid characters";}
			}
			elsif($form{'action'} eq "serverinfo"){	#shows processlist
				$form{'queryrecords'} = &runQuery($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'}, "SHOW PROCESSLIST;");
			}
			elsif($form{'action'} eq "droptable"){
				if($form{'tables'} =~ m/^(\w+)$/){	#safety check on table name
					$form{'rows'} = &getTableRows($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'}, $form{'tables'});
					&updateKey($form{'key'});
				}
				else{$error = "Table name contains invalid characters";}
			}
			elsif($form{'action'} eq "droptableconfirm"){
				if($form{'answer'} eq "yes"){	#user confirmed drop
					if($form{'tables'} =~ m/^(\w+)$/){	#safety check on table name
						$form{'queryrecords'} = &runNonSelect($form{'host'}, $form{'user'}, $form{'password'}, $form{'database'}, "DROP TABLE $1;");
					}
					else{$error = "Table name contains invalid characters";}
				}
				else{$error = "You did not confirm that you wanted the table dropped";}
			}
			else{$error = "Invalid action: $form{'action'}";}	#a strange action has been found
		}
		&parsePage($form{'action'});
	}
	else{	#display the starting page
		$form{'key'} = &createKey();	#created new server side cookie file
		&parsePage("login");
	}
}
else{&parsePage("error");}
exit(0);
###############################################################################################################
sub getData{	#gets cgi form data into a hash
	my $cgi = CGI::new();
	foreach($cgi -> param()){
		if($cgi -> param($_) !~ m/\;/){
			$form{$_} = $cgi -> param($_);
		}
		else{
			$error = "One of the values submitted from the last page contained invalid characters";
			return 0;
		}
		#print STDERR "$_ = $form{$_}\n";
	}	#save the form data to a hash
	return 1;
}
###############################################################################################################
sub createKey{	#creates a new server side cookie
	my $key = time;
	if(!-e "keys/$key"){	#key does not exist already
		if(open(COOKIE, ">keys/$key")){close(COOKIE);}
		else{$error = "Could not create session file: $!";}
		return $key;
	}
	else{$error = "New session already exists";}
	return undef;	#must of got an error somewhere in this sub
}
###############################################################################################################
sub readKey{	#read the contents of a server side cookie back into the form hash
	if(open(COOKIE, "<keys/$_[0]")){
		while(<COOKIE>){
			if(m/^([A-Z]+) = (.+)$/){
				#print STDERR "$0: cookie line: $1 = $2\n";
				$form{lc($1)} = $2;
			}	#store the valid lines
			else{print STDERR "$0: Ignoring invalid session file line: $_\n";}	#log warning, not really a problem
		}
		close(COOKIE);
		return 1;	#everything ok
	}
	else{$error = "Cant read session file: $!";}
	return 0;
}
###############################################################################################################
sub updateKey{	#saves last form's data, overwriting the existing key file
	$_[0] =~ m/^(\d+)$/;	#untaint
	my @wanted = ("database", "password", "host", "user", "type", "fields", "criteria", "tables");
	if(open(COOKIE, ">keys/$1")){
		foreach my $name (keys %form){
			my $found = 0;
			foreach(@wanted){	#dont save unwanted elements
				if($name eq $_){
					$found = 1;
					last;
				}
			}
			if($found){print COOKIE uc($name) . " = " . $form{$name} . "\n";}	#save this hash element
		}
		close(COOKIE);
		return 1;	#everything ok
	}
	else{$error = "Cant write session file: $!";}
	return 0;
}
##############################################################################################################
sub deleteKey{
	$_[0] =~ m/^(\d+)$/;	#untaint
	unlink("keys/$1");
}
###############################################################################################################
sub replace{	#make sure we dont get any undefined values when replacing template placeholders
	if(defined($form{$_[0]})){return $form{$_[0]};}	#return hash value
	else{
		print STDERR "$0: $_[0] is undefined in placeholder replace\n";
		return "";	#return nothing
	}
}
###############################################################################################################
sub parsePage{	#displays a html page
	my $page = shift;
	print "Content-type: text/html\n\n";
	if($error){	#an error has not been encountered
		$page = "error";
		print STDERR "$0: $error\n";	#log this error too
	}
	if(open(TEMPLATE, "<templates/$page.html")){
		while(<TEMPLATE>){	#read the file a line at a time
			$_ =~ s/<!--self-->/$ENV{'SCRIPT_NAME'}/g;	#replace the name for this script
			$_ =~ s/<!--server-->/$ENV{'HTTP_HOST'}/g;	#replace webserver name
			$_ =~ s/<!--error-->/$error/g;	#replace the error message
			$_ =~ s/<!--version-->/2.0/g;	#replace version number
			$_ =~ s/<!--(\w+)-->/&replace($1)/eg;	#replace the placeholders in the template
         $_ =~ s|</body>|<br><br>\n<div align="center"><font size="2">&copy; <a href="http://www.thedumbterminal.co.uk" target="_blank">Dumb Terminal Creations</a></font></div>\n</body>|;
			print;
		}
		close(TEMPLATE);
	}
	else{
		print << "(NO TEMPLATE)";
<html>
	<body>
		Could not open HTML template: webmysql_templates/$page.html
	</body>
</html>
(NO TEMPLATE)
	}
}
############################################################################################################
sub testConnect{	#tests if we can connect to the mysql server
	my($host, $user, $password, $database) = @_;
	my $dbh = DBI -> connect("DBI:mysql:database=$database;host=$host", $user, $password);
	if($dbh){
		$dbh -> disconnect();
		return 1;
	}
	else{
		$error = "Cant connect to MySQL server: " . $DBI::errstr;
		return 0;
	}
}
##########################################################################################################
sub getTables{	#returns an array of tables for the current database
	my($host, $user, $password, $database) = @_;
	my $dbh = DBI -> connect("DBI:mysql:database=$database;host=$host", $user, $password);
	if($dbh){
		my $query = $dbh -> prepare("SHOW TABLES;");
		if($query -> execute()){
			my @tables;
			while(my $table = $query -> fetchrow_array()){push(@tables, $table);}	#create an array of the tables found
			$query -> finish();
			return @tables;	#send back the tables to the calling sub
		}
		else{$error = "Cant find table list: " . $dbh -> errstr;}
		$dbh -> disconnect();
	}
	else{$error = "Cant connect to MySQL server: " . $DBI::errstr;}
	return undef;
}
##########################################################################################################
sub getFields{	#returns an array of tables for the current database
	my($host, $user, $password, $database, $tables) = @_;
	my $dbh = DBI -> connect("DBI:mysql:database=$database;host=$host", $user, $password);
	if($dbh){
		my @fields;
		foreach(split(/, /, $tables)){	#get the fields for all of the selected tables
			my $query = $dbh -> prepare("DESCRIBE $_;");
			if($query -> execute()){
				while(my @dInfo = $query -> fetchrow_array()){push(@fields, "$_.$dInfo[0]");}	#create an array of the fields found
				$query -> finish();
			}
			else{
				$error = "Cant retrieve fields list for $_ table: " . $dbh -> errstr;
				last;
			}
		}
		$dbh -> disconnect();
		if(!$error){return @fields;}	#send back the fields to the calling sub
	}
	else{$error = "Cant connect to MySQL server: " . $DBI::errstr;}
	return undef;
}
##################################################################################################################
sub composeSelect{	#generates the sql code for a select query
	my $code = "SELECT ";
	if($form{'distinct'}){$code .= "DISTINCT ";}	#distinct results only
	$code .= "$form{'fields'}";	#add the fields to show
	if($form{'groupby'} ne "" && $form{'groupfunc'} ne "" && $form{'funcfield'} ne ""){	#user is grouping with a group function
		$code .= ", $form{'groupfunc'}($form{'funcfield'})";
	}
	$code .= " FROM ";
	my @tables = split(/, /, $form{'tables'});
	$code .= $tables[0];
	if($form{'tables'} =~ m/, /){
		for(my $tCount = 1; $tCount <= $#tables; $tCount++){
			$code .= " LEFT JOIN $tables[$tCount] ON $form{'joinfield1_' . $tables[$tCount]} = $form{'joinfield2_' . $tables[$tCount]}";
		}
	}
	my $criteria = "";
	my $count = 0;
	while($form{'critname' . $count} ne ""){
		$criteria .= $form{'critname' . $count} . " " . $form{'crithow' . $count} . " '" . $form{'crit' . $count} . "'";
		if(exists($form{'critname' . ($count + 1)}) && $form{'critname' . ($count + 1)}){$criteria .= " " . $form{'critappend' . $count} . " ";}
		$count++;
	}
	if($criteria ne ""){$code .= " WHERE $criteria";}
	if($form{'groupby'} ne ""){$code .= " GROUP BY $form{'groupby'}";}	#add grouping
	if($form{'orderby'} ne ""){
		$code .= " ORDER BY $form{'orderby'}";	#add sorting
		if($form{'desc'}){$code .= " DESC";}	#reverse sorting
	}
	$code .= ";";
	return $code;
}
##################################################################################################################
sub runQuery{
	my($host, $user, $password, $database, $code) = @_;
	my $dbh = DBI -> connect("DBI:mysql:database=$database;host=$host", $user, $password);
	if($dbh){
		my $query = $dbh -> prepare($code);
		if($query -> execute()){
			my $html = "<tr>";
			my $names = $query ->{'NAME'};	#all returned field names
			for(my $i = 0;  $i < $query ->{'NUM_OF_FIELDS'};  $i++){$html .= "<th>$$names[$i]</th>";}	#get field names
			$html .= "</tr>\n";	#finished field names
			while(my @fields = $query -> fetchrow_array()){
				$html .= "<tr>";
				foreach(@fields){
					if($_){$html .= "<td>$_</td>";}	#this field has a value
					else{$html .= "<td>&nbsp;</td>";}	#this field has a null value
				}
				$html .= "</tr>\n";
			}
			$html .= "<tr><td align=\"center\" colspan=\"" . $query ->{'NUM_OF_FIELDS'} . "\">" . $query -> rows() . "Rows found</td></tr>\n";	#print rows found
			$query -> finish();
			return $html;
		}
		else{$error = "Problem with query: " . $dbh -> errstr;}
		$dbh -> disconnect();
	}
	else{$error = "Cant connect to MySQL server: " . $DBI::errstr;}
	return undef;
}
##########################################################################################################
sub getTableRows{	#returns how many rows in a table
	my($host, $user, $password, $database, $table) = @_;
	my $dbh = DBI -> connect("DBI:mysql:database=$database;host=$host", $user, $password);
	if($dbh){
		my $query = $dbh -> prepare("SELECT COUNT(*) FROM $table;");
		my $rows;
		if($query -> execute()){
			$rows = $query -> fetchrow_array();
			$query -> finish();
		}
		else{$error = "Cant retrieve number of rows for $_ table: " . $dbh -> errstr;}
		$dbh -> disconnect();
		if(!$error){return $rows;}	#send back the fields to the calling sub
	}
	else{$error = "Cant connect to MySQL server: " . $DBI::errstr;}
	return undef;
}
#############################################################################################################
sub runNonSelect{
	my($host, $user, $password, $database, $code) = @_;
	my $dbh = DBI -> connect("DBI:mysql:database=$database;host=$host", $user, $password);
	if($dbh){
		my $affected;
		if(!($affected = $dbh -> do($code))){$error = "Problem with query: " . $dbh -> errstr;}
		$dbh -> disconnect();
		if(!$error){return $affected;}	#send back the fields to the calling sub
	}
	else{$error = "Cant connect to MySQL server: " . $DBI::errstr;}
	return undef;
}
