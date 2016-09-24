#the dumb terminal webmysql module
#mt 16/11/2003 2.4	moved version into this module
package DTWebMySQL::Main;
BEGIN {
   use Exporter();
	our %form;	#data from the previous page
	our $error = "";	#error flag
	our $version ="2.4";	#version of this software
	@ISA = qw(Exporter);
   @EXPORT = qw(%form $error $version);
}
###############################################################################
return 1;
END {}

