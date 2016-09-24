#!/usr/bin/perl -w
#mysql database web interface
use strict;
#use lib "/usr/lib/perl5/site_perl/5.6.0/i586-linux";  #for perl2exe for the mysql module
use DBI;
use DBD::mysql::mysql.so
my %formData;
$formData{'version'} = "1.6";
$formData{'action'} = "start";	#default
$formData{'output'} = "";
$formData{'database'} = "";
$formData{'username'} = "";
$formData{'password'} = "";
$formData{'server'} = "";
$formData{'onload'} = "";
my @matchHow = ("=", ">=", "<=", ">", "<", "!=", "LIKE", "NOT LIKE", "REGEXP");	#how to match input
&get_data;
if($formData{"action"} eq "Use"){&show_databases;}	#list the available databases
elsif($formData{"action"} eq "Query"){&show_tables;}	#list the available tables from the current database
elsif($formData{"action"} eq "Describe"){&describe_table;}
elsif($formData{"action"} eq "Join-Select"){&show_join_tables;}
elsif($formData{"action"} eq "Select"){&compose_select;}
elsif($formData{"action"} eq "composejoin"){&compose_join;}
elsif($formData{"action"} eq "runselect"){&run_select;}	#display the query results
elsif($formData{"action"} eq "runjoin"){&run_join;}
elsif($formData{"action"} eq "Status"){&gen_query("SHOW STATUS;");}
elsif($formData{"action"} eq "Variables"){&gen_query("SHOW VARIABLES;");}
elsif($formData{"action"} eq "Processes"){&gen_query("SHOW PROCESSLIST;");}
elsif($formData{"action"} eq "refresh"){	#refreshes the menu frame with new details
	$formData{"onload"} = " onload=\"parent.menu.location='$ENV{'SCRIPT_NAME'}?action=menu&username=$formData{'username'}&password=$formData{'password'}&server=$formData{'server'}&database=$formData{'database'}'\"";
	$formData{"action"} = "main";
}
if($formData{'output'} ne "csv" || ($formData{'output'} eq "csv" && defined($formData{'error'}))){&parse_frame($formData{'action'});}
exit(0);
##########################################################################################
sub parse_frame{
   my $file = shift;
   if(defined($formData{'error'})){$file = "error";}  #display the error message page as we have an error
   elsif($file eq "runjoin"){$file = "runselect";} #join results are displayed on the same page as select results
   $formData{'self'} = $ENV{'SCRIPT_NAME'};  #save the name of this script
	print "Content-type: text/html\n\n";
   if(open(TEMPLATE, "<webmysql_templates/$file.html")){
      while(<TEMPLATE>){
         $_ =~ s/<!--(\w+)-->/&get_element($1)/eg;
         $_ =~ s|</body>|<!-- @ Dumb Terminal Creations (http://www.thedumbterminal.co.uk) -->\n</body>|;
         print;
      }
      close(TEMPLATE);
   }
	else{print "Fatal: Cant open webmysql_templates/$file.html: $!\n";}
}
##########################################################################################
sub get_element{
	if(defined($formData{$_[0]})){return $formData{$_[0]};}	#the hash element exists
	else{	# the hash element does not exist
		print STDERR "$0: hash element does not exist: $_[0]\n";
		return "";
	}
}
##########################################################################################
sub get_data{
	my @pairs;
	if($ENV{'REQUEST_METHOD'} eq 'POST'){
		my $buffer;
   	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
      @pairs = split(/&/, $buffer);
	}
	elsif($ENV{'REQUEST_METHOD'} eq 'GET'){@pairs = split(/&/, $ENV{'QUERY_STRING'});}
	foreach (@pairs){
		my($name, $value) = split(/=/);
		$name =~ tr/+/ /;
     	$name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
     	$value =~ tr/+/ /;
     	$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
     	$value =~ s/<!--(.|\n)*-->//g;
     	$value =~ s/;//g;	#so user's cant use multiple commands!
		$formData{$name} = $value;	#store
	}
}
###########################################################################################
sub show_databases{
	my $dbh = DBI -> connect("DBI:mysql:database=;host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		my $query = $dbh -> prepare("SHOW DATABASES;");
   	if($query -> execute){
      	$formData{'databases'} = "";
   		while(my $dbName = $query -> fetchrow_array){
				my $first = "";
				if($dbName eq $formData{'database'}){$first = " checked";}	#current database is selected by defualt
				$formData{'databases'} .= "<tr><td bgcolor=\"#7777BB\"><input$first type=\"radio\" name=\"database\" value=\"$dbName\"></td><td>$dbName</td></tr>\n";
			}
   		$query -> finish();
		}
		else{$formData{'error'} = $DBI::errstr;}
		$dbh -> disconnect();
	}
	else{$formData{'error'} = $DBI::errstr;}
}
###########################################################################################
sub show_tables{
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		my $query = $dbh -> prepare("SHOW TABLES;");
   	if($query -> execute){
   		my $first = " checked";	#make the first checkbox select by default
      	$formData{'tables'} = "";
			while(my $tableName = $query -> fetchrow_array){
				$formData{'tables'} .= "<tr><td bgcolor=\"#7777BB\"><input$first type=\"radio\" name=\"table\" value=\"$tableName\"></td><td>$tableName</td></tr>\n";
				$first = "";
			}
   		$query -> finish();
		}
		else{$formData{'error'} = $DBI::errstr;}
		$dbh -> disconnect();
	}
	else{$formData{'error'} = $DBI::errstr;}
}
###########################################################################################
sub compose_select{
	my @matchPlus = ("AND", "OR");	#if the wants to use more than one field criteria
	my @fieldNames;
	my $fieldCount = 0;
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		my $query = $dbh -> prepare("DESCRIBE $formData{'table'};");
   	$query -> execute || print "error was " . $dbh -> errstr;
      $formData{'rows'} = $query -> rows;
      $formData{'showfields'} = "";
		while(my @fieldInfo = $query -> fetchrow_array){
			$formData{'showfields'} .= "<input type=\"checkbox\" name=\"" . $fieldCount . "_show\" value=\"$fieldInfo[0]\">$fieldInfo[0], ";
      	push(@fieldNames, $fieldInfo[0]);
			$fieldCount++;
		}
   	$query -> finish();
		$dbh -> disconnect();
		$formData{'fieldlist'} = "";
		foreach(@fieldNames){$formData{'fieldlist'} .= "<option value=\"$_\">$_</option>\n";}	#create a list of all the field names
      $formData{'critfields'} = "";
      for(my $critCount = 0; $critCount <= 4; $critCount++){
   		$formData{'critfields'} .= "<select name=\"" . $critCount . "_name\"><option value=\"\"> ";
			$formData{'critfields'} .= $formData{'fieldlist'};	#add all the fields to the drop down box
   		$formData{'critfields'} .= "</select> <select name=\"" . $critCount . "_how\">";
			foreach(@matchHow){$formData{'critfields'} .= "<option value=\"$_\">$_";}
      	$formData{'critfields'} .= "</select> <input type=\"text\" name=\"" . $critCount . "_value\"> ";
			if($critCount != 4){
				$formData{'critfields'} .= "<select name=\"" . $critCount . "_plus\"><option value=\"\"> ";
				foreach(@matchPlus){$formData{'critfields'} .= "<option value=\"$_\">$_";}
				$formData{'critfields'} .= "</select><br>";
			}
			$formData{'critfields'} .= "\n";
		}
      $formData{'orderbyoptions'} = "";
      foreach(@fieldNames){$formData{'orderbyoptions'} .= "<option value=\"$_\">$_";}
	}
	else{$formData{'error'} = $DBI::errstr;}
}
##################################################################################################################
sub run_select{
	my $crit;
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		$formData{'sql'} = "SELECT ";
		if(defined($formData{'distinct'})){$formData{'sql'} .= "DISTINCT ";}	#distinct results only
   	for(my $fieldCount = 0; $fieldCount < $formData{'totalfields'}; $fieldCount++){
			if(defined($formData{$fieldCount . "_show"})){$formData{'sql'} .= $formData{$fieldCount . "_show"} . ", ";}	#add the field to the display list
		}
		if($formData{'sql'} eq "SELECT "){$formData{'sql'} .= "*";}	#just incase no fields where ticked
		else{$formData{'sql'} = substr($formData{'sql'}, 0, length($formData{'sql'}) - 2);}	#get rid of the last comma and space
		if($formData{'function'} ne "" && $formData{'groupby'} ne ""){	# use a group by field
			if($formData{'functionfield'} ne ""){$formData{'sql'} .= ", " . $formData{'function'} . "(" . $formData{'functionfield'} . ")";}	# use a field in the group by function
			else{$formData{'sql'} .= ", " . $formData{'function'} . "(*)";}	#use a star
		}
		$formData{'sql'} .= " FROM $formData{'table'}";
		for(my $critCount = 0; $critCount <= 4; $critCount++){
			if($formData{$critCount . "_name"} ne ""){
				$crit .= " " . $formData{$critCount . "_name"} . " " . $formData{$critCount . "_how"} . " \"" . $formData{$critCount . "_value"} . "\"";
				my $critCount2 = $critCount;
				$critCount2++;
				if($formData{$critCount . "_plus"} ne "" && $formData{$critCount2 . "_name"} ne ""){$crit .= " " . $formData{$critCount . "_plus"} . " ";}
				else{last;}	#end criteria here
			}
		}
		if($crit){$formData{'sql'} .= " WHERE" . $crit;}	#add in the criteria
		if($formData{'orderby'} ne ""){	#sort the results
			$formData{'sql'} .= " ORDER BY $formData{'orderby'}";
			if($formData{'desc'} eq "on"){$formData{'sql'} .= " DESC";}	#reverse the sort order
		}
		if($formData{'function'} ne "" && $formData{'groupby'} ne ""){$formData{'sql'} .= " GROUP BY " . $formData{'groupby'};}	# use a group by field
		if($formData{'limit'} ne ""){$formData{'sql'} .= " LIMIT $formData{'limit'}";}	#limit the results
		$formData{'sql'} .= ";";
		my $query = $dbh -> prepare($formData{'sql'});
   	if($query -> execute){
			if($formData{'output'} eq "csv"){   #just print plain text
				print "Content-type: application/data\n\n";
				print "$formData{'sql'}\n";
		   	my $names = $query ->{'NAME'};	#all returned field names
				for(my $i = 0;  $i < $query ->{'NUM_OF_FIELDS'};  $i++){
					print "\"$$names[$i]\"";
					if($i < ($query ->{'NUM_OF_FIELDS'} - 1)){print ",";}	#add the separator
				}
				print "\n";
				while(my @fieldInfo = $query -> fetchrow_array){print "\"" . join("\",\"", @fieldInfo) . "\"\n";}
			}
			else{	#html and drip tray
		   	my $names = $query ->{'NAME'};	#all returned field names
            $formData{'headings'} = "";
				for(my $i = 0;  $i < $query ->{'NUM_OF_FIELDS'};  $i++){$formData{'headings'} .= "<th bgcolor=\"#7777BB\">$$names[$i]</th>";}
            $formData{'fields'} = "";
            while(my @fieldInfo = $query -> fetchrow_array){
					$formData{'fields'} .= "<tr>";
					foreach(@fieldInfo){$formData{'fields'} .= "<td>$_</td>\n";}
					$formData{'fields'} .= "</tr>\n";
				}
				$formData{'numfields'} = $query ->{'NUM_OF_FIELDS'};
            $formData{'rows'} = $query -> rows;
			}
	  	 	$query -> finish();
   	}
		else{$formData{'error'} = "error was " . $dbh -> errstr . "<br>\nWith the SQL code of: $formData{'sql'}";}
		$dbh -> disconnect();
	}
	else{$formData{'error'} = $DBI::errstr;}
}
##################################################################################################################
sub describe_table{
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		my $query = $dbh -> prepare("DESCRIBE $formData{'table'};");
   	$query -> execute || print "error was " . $dbh -> errstr;
   	my $names = $query ->{'NAME'};	#all returned field names
      $formData{'headings'} = "";
		for(my $i = 0;  $i < $query ->{'NUM_OF_FIELDS'};  $i++){$formData{'headings'} .= "<th>$$names[$i]</th>";}
      $formData{'fields'} = "";
		while(my @fieldInfo = $query -> fetchrow_array){
			$formData{'fields'} .= "<tr>";
			foreach(@fieldInfo){$formData{'fields'} .= "<td>$_</td>";}
			$formData{'fields'} .= "</tr>\n";
		}
		$formData{'numfields'} = $query ->{'NUM_OF_FIELDS'};
      $formData{'rows'} = $query -> rows;
   	$query -> finish();
		$dbh -> disconnect();
	}
	else{$formData{'error'} = $DBI::errstr;}
}
###########################################################################################
sub show_join_tables{
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		my $query = $dbh -> prepare("SHOW TABLES;");
   	$query -> execute || print "error was " . $dbh -> errstr;
		my $count = 1;
      $formData{'tables'} = "";
		while(my $tableName = $query -> fetchrow_array){
			$formData{'tables'} .= "\t\t\t\t<tr><td bgcolor=\"#7777BB\">";
			if($tableName ne $formData{'table'}){
				$formData{'tables'} .= "<input type=\"checkbox\" name=\"table$count\" value=\"$tableName\">";	#user can select this table
				$count++;
			}
			else{$formData{'tables'} .= "&nbsp;";}	#blank the cell
			$formData{'tables'} .= "</td><td>$tableName</td></tr>\n";
		}
   	$query -> finish();
		$dbh -> disconnect();
	}
	else{$formData{'error'} = $DBI::errstr;}
}
###########################################################################################
sub compose_join{
	my @matchPlus = ("AND", "OR");	#if the wants to use more than one field criteria
	my @joinHow = ("LEFT JOIN", "RIGHT JOIN");	#how to join the tables
	my @sides = ("left", "right");	#join critera
	my @fieldNames;
	my $fieldCount = 0;
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
      $formData{'chosentables'} = "";
		foreach my $name (keys %formData){	#print each on the chosen tables
			if(substr($name, 0, 5) eq "table"){$formData{'chosentables'} .= "<input type=\"hidden\" name=\"$name\" value=\"$formData{$name}\">\n";}
		}
		$formData{'totalfields'} = 0;
      $formData{'showfields'} = "";
	  	foreach my $name (keys %formData){	#list each field on the chosen tables
			if(substr($name, 0, 5) eq "table"){
				my $query = $dbh -> prepare("DESCRIBE $formData{$name};");
   			$query -> execute || print "error was " . $dbh -> errstr;
            while(my @fieldInfo = $query -> fetchrow_array){
					$formData{'showfields'} .= "<input type=\"checkbox\" name=\"" . $fieldCount . "_show\" value=\"$formData{$name}.$fieldInfo[0]\">$formData{$name}.$fieldInfo[0], ";
      			push(@fieldNames, "$formData{$name}.$fieldInfo[0]");
					$fieldCount++;
				}
   			$formData{'totalfields'} += $query -> rows;	#increase the total
   			$query -> finish();
			}
		}
		$dbh -> disconnect();
		$formData{'fieldlist'} = "";
		foreach(@fieldNames){$formData{'fieldlist'} .= "<option value=\"$_\">$_</option>\n";}	#create a list of all the field names
      $formData{'joinvalues'} = "";
	  	foreach my $name (keys %formData){	#list each field on the chosen tables
			if(substr($name, 0, 5) eq "table" && $name ne "table0"){
				$formData{'joinvalues'} .= "<tr>\n<th bgcolor=\"#7777BB\">JOIN</th>\n<td>\n<select name=\"$name\_join\">\n";
				foreach(@joinHow){$formData{'joinvalues'} .= "<option value=\"$_\">$_</option>";}
				$formData{'joinvalues'} .= "</select> $formData{$name} ";
				$formData{'joinvalues'} .= "</td>\n</tr>\n<tr>\n<th bgcolor=\"#7777BB\">ON</th>\n<td>";
   		   for(my $onCount = 0; $onCount <= 1; $onCount++){
      		   foreach (@sides){
   	 			   $formData{'joinvalues'} .= "<select name=\"$name" . $onCount . "_on$_\">";
   				   if($onCount > 0){$formData{'joinvalues'} .= "<option value=\"\"> </option>";}
   				   foreach(@fieldNames){$formData{'joinvalues'} .= "<option value=\"$_\">$_</option>";}
       			   $formData{'joinvalues'} .= "</select>";
   				   if($_ eq "left"){$formData{'joinvalues'} .= " = ";}
   			   }
   			   if($onCount != 1){
   				   $formData{'joinvalues'} .= "<select name=\"$name" . $onCount . "_plus\">\n<option value=\"\"> </option>";
   				   foreach(@matchPlus){$formData{'joinvalues'} .= "<option value=\"$_\">$_</option>";}
   				   $formData{'joinvalues'} .= "</select><br>";
   			   }
   			   $formData{'joinvalues'} .= "\n";
   		   }
      		$formData{'joinvalues'} .= "</td>\n</tr>\n";
      	}
		}
      $formData{'critfields'} = "";
		for(my $critCount = 0; $critCount <= 4; $critCount++){
   		$formData{'critfields'} .= "<select name=\"" . $critCount . "_name\"><option value=\"\"> </option";
			foreach(@fieldNames){$formData{'critfields'} .= "<option value=\"$_\">$_</option>";}
   		$formData{'critfields'} .= "</select> <select name=\"" . $critCount . "_how\">";
			foreach(@matchHow){$formData{'critfields'} .= "<option value=\"$_\">$_</option>";}
      	$formData{'critfields'} .= "</select> <input type=\"text\" name=\"" . $critCount . "_value\"> ";
			if($critCount != 4){
				$formData{'critfields'} .= "<select name=\"" . $critCount . "_plus\"><option value=\"\"> </option>";
				foreach(@matchPlus){$formData{'critfields'} .= "<option value=\"$_\">$_</option>";}
				$formData{'critfields'} .= "</select><br>";
			}
			$formData{'critfields'} .= "\n";
		}
      $formData{'orderbyoptions'} = "";
		foreach(@fieldNames){$formData{'orderbyoptions'} .= "<option value=\"$_\">$_</option>";}
	}
	else{$formData{'error'} = $DBI::errstr;}
}
##################################################################################################################
sub run_join{
	my $crit;
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		$formData{'sql'} = "SELECT ";
   	for(my $fieldCount = 0; $fieldCount < $formData{'totalfields'}; $fieldCount++){
			if(defined($formData{$fieldCount . "_show"})){$formData{'sql'} .= $formData{$fieldCount . "_show"} . ", ";}	#add the field to the display list
		}
		if($formData{'sql'} eq "SELECT "){	#just incase no fields where ticked
		  	foreach my $name (keys %formData){	#list each field on the chosen tables
				if($name =~ m/^table\d*$/){$formData{'sql'} .= $formData{$name} . ".*, ";}
			}
		}
		if($formData{'function'} ne "" && $formData{'groupby'} ne ""){	# use a group by field
			if($formData{'functionfield'} ne ""){$formData{'sql'} .= $formData{'function'} . "(" . $formData{'functionfield'} . "), ";}	# use a field in the group by function
			else{$formData{'sql'} .= $formData{'function'} . "(*), ";}	#use a star
		}
	   $formData{'sql'} = substr($formData{'sql'}, 0, length($formData{'sql'}) - 2);	#get rid of the last comma and space
		$formData{'sql'} .= " FROM $formData{'table0'}";
	  	foreach my $name (keys %formData){	#join each of the tables
			if($name =~ m/^table\d*$/ && $name ne "table0"){	#found a table field
				$formData{'sql'} .= " " . $formData{$name . "_join"} . " $formData{$name} ON ";
				for(my $joinCount = 0; $joinCount <= 2; $joinCount++){	#allow upto two criteria for joining tables
					$formData{'sql'} .= "(" . $formData{$name . $joinCount . "_onleft"} . " = " .$formData{$name . $joinCount . "_onright"} . ")";
					my $joinCount2 = $joinCount;
					$joinCount2++;
					if($formData{$name . $joinCount . "_plus"} ne "" && $formData{$name . $joinCount2 . "_onleft"} ne "" && $formData{$name . $joinCount2 . "_onright"} ne ""){$formData{'sql'} .= " " . $formData{$name . $joinCount . "_plus"} . " ";}	#put in the boolean operator
					else{last;}	#end join criteria here
				}
			}
		}
		for(my $critCount = 0; $critCount <= 4; $critCount++){
			if($formData{$critCount . "_name"} ne ""){
				$crit .= " " . $formData{$critCount . "_name"} . " " . $formData{$critCount . "_how"} . " \"" . $formData{$critCount . "_value"} . "\"";
				my $critCount2 = $critCount;
				$critCount2++;
				if($formData{$critCount . "_plus"} ne "" && $formData{$critCount2 . "_name"} ne ""){$crit .= " " . $formData{$critCount . "_plus"} . " ";}
				else{last;}	#end criteria here
			}
		}
		if($crit){$formData{'sql'} .= " WHERE" . $crit;}	#add in the criteria
		if($formData{'orderby'} ne ""){	#sort the results
			$formData{'sql'} .= " ORDER BY $formData{'orderby'}";
			if($formData{'desc'} eq "on"){$formData{'sql'} .= " DESC";}	#reverse the sort order
		}
		if($formData{'function'} ne "" && $formData{'groupby'} ne ""){$formData{'sql'} .= " GROUP BY " . $formData{'groupby'};}	# use a group by field
		if($formData{'limit'} ne ""){$formData{'sql'} .= " LIMIT $formData{'limit'}";}	#limit the results
		$formData{'sql'} .= ";";
		my $query = $dbh -> prepare($formData{'sql'});
   	if($query -> execute){
			if($formData{'output'} eq "csv"){
				print "Content-type: application/data\n\n";
				print "$formData{'sql'}\n";
		   	my $names = $query ->{'NAME'};	#all returned field names
				for(my $i = 0;  $i < $query ->{'NUM_OF_FIELDS'};  $i++){
					print "\"$$names[$i]\"";
					if($i < ($query ->{'NUM_OF_FIELDS'} - 1)){print ",";}	#add the separator
				}
				print "\n";
				while(my @fieldInfo = $query -> fetchrow_array){print "\"" . join("\",\"", @fieldInfo) . "\"\n";}
			}
			else{	#html and drip tray
		   	my $names = $query ->{'NAME'};	#all returned field names
            $formData{'headings'} = "";
            for(my $i = 0;  $i < $query ->{'NUM_OF_FIELDS'};  $i++){$formData{'headings'} .= "<th bgcolor=\"#7777BB\">$$names[$i]</th>";}
				$formData{'headings'} .= "</tr>\n";
				$formData{'fields'} = "";
				while(my @fieldInfo = $query -> fetchrow_array){
					$formData{'fields'} .= "<tr>";
					foreach(@fieldInfo){$formData{'fields'} .= "<td>$_</td>\n";}
					$formData{'fields'} .= "</tr>\n";
				}
				$formData{'numfields'} = $query ->{'NUM_OF_FIELDS'};
            $formData{'rows'} = $query -> rows;
			}
	  	 	$query -> finish();
   	}
		else{$formData{'error'} = "error was " . $dbh -> errstr . "<br>\nWith the SQL code of: $formData{'sql'}";}
		$dbh -> disconnect();
	}
	else{$formData{'error'} = $DBI::errstr;}
}
#########################################################################################################################################
sub gen_query{
	my $qString = shift;
	my $dbh = DBI -> connect("DBI:mysql:database=$formData{'database'};host=$formData{'server'}", $formData{"username"}, $formData{"password"});
	if($dbh){
		my $query = $dbh -> prepare($qString);
   	if($query -> execute){
	   	my $names = $query ->{'NAME'};	#all returned field names
         $formData{'headings'} = "";
         for(my $i = 0;  $i < $query ->{'NUM_OF_FIELDS'};  $i++){$formData{'headings'} .= "<th bgcolor=\"#7777BB\">$$names[$i]</th>";}
			$formData{'headings'} .= "</tr>\n";
			$formData{'fields'} = "";
			while(my @fieldInfo = $query -> fetchrow_array){
				$formData{'fields'} .= "<tr>";
				foreach(@fieldInfo){$formData{'fields'} .= "<td>$_</td>\n";}
				$formData{'fields'} .= "</tr>\n";
			}
			$formData{'numfields'} = $query ->{'NUM_OF_FIELDS'};
         $formData{'rows'} = $query -> rows;
	  	 	$query -> finish();
   	}
		else{$formData{'error'} = "error was " . $dbh -> errstr . "<br>\nWith the SQL code of: $qString";}
		$dbh -> disconnect();
	}
	else{$formData{'error'} = $DBI::errstr;}
}
