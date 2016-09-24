#the dumb terminal webmysql module
package DTWebMySQL::Sql;
BEGIN {
	use DTWebMySQL::Main;
   use Exporter();
	@ISA = qw(Exporter);
   @EXPORT = qw(testConnect getTables getFields getDatabases runQuery getTableRows runNonSelect);
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
sub getFields{	#returns an array of fields for the current table
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
##########################################################################################################
sub getDatabases{	#returns an array of databases for the current connection
	my($host, $user, $password) = @_;
	my $dbh = DBI -> connect("DBI:mysql:database=;host=$host", $user, $password);
	if($dbh){
		my $query = $dbh -> prepare("SHOW DATABASES;");
		if($query -> execute()){
			my @dbs;
			while(my $db = $query -> fetchrow_array()){push(@dbs, $db);}	#create an array of the tables found
			$query -> finish();
			return @dbs;	#send back the tables to the calling sub
		}
		else{$error = "Cant find database list: " . $dbh -> errstr;}
		$dbh -> disconnect();
	}
	else{$error = "Cant connect to MySQL server: " . $DBI::errstr;}
	return undef;
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
				$html .= "<tr bgcolor=\"#FFFFFF\">";
				foreach(@fields){
					if($_){	#this field has a value
						$_ =~ s/</&lt;/g;	#html dont like less than signs
						$_ =~ s/>/&gt;/g;	#html dont like greater than signs
						$html .= "<td>$_</td>";
					}
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
###############################################################################
return 1;
END {}

