#the dumb terminal webmysql module
package DTWebMySQL::Main;
BEGIN {
   use Exporter();
	our %form;	#data from the previous page
	our $error = "";	#error flag
	@ISA = qw(Exporter);
   @EXPORT = qw(%form $error);
}
###############################################################################
return 1;
END {}

