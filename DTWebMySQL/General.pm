#the dumb terminal webmysql module
package DTWebMySQL::General;
BEGIN {
   use Exporter();
	use DTWebMySQL::Main;
	@ISA = qw(Exporter);
   @EXPORT = qw(getData replace parsePage);
}
###############################################################################################################
sub getData{	#gets cgi form data into a hash
	#foreach (keys %ENV){print STDERR "$_ = $ENV{$_}\n";}
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
	}
	return 1;
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
	my $version = "2.3";	#version of this code
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
			$_ =~ s/<!--version-->/$version/g;	#replace version number
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
		Could not open HTML template: webmysql-$version/templates/$page.html
	</body>
</html>
(NO TEMPLATE)
	}
}
###############################################################################
return 1;
END {}

