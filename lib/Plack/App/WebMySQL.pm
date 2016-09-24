#the dumb terminal webmysql module
#mt 16/11/2003 2.4	moved version into this module
package Plack::App::WebMySQL;
use Exporter();
our %form;	#data from the previous page
our $error = "";	#error flag
our $VERSION ="3.0";	#version of this software
@ISA = qw(Exporter);
@EXPORT = qw(%form $error $VERSION);
###############################################################################
return 1;
