#the dumb terminal webmysql module
#mt 16/11/2003 2.4	moved version into this module
package Plack::App::WebMySQL;
use strict;
use warnings;
use CGI::Compile;
use CGI::Emulate::PSGI;
use Plack::Builder;
use Plack::App::MCCS;
use Exporter();
our %form;	#data from the previous page
our $error = "";	#error flag
our $VERSION ="3.0";	#version of this software
our @ISA = qw(Exporter);
our @EXPORT = qw(%form $error $VERSION);
###############################################################################
sub new{
	my $sub = CGI::Compile->compile("./cgi-bin/webmysql/webmysql.cgi");
	my $app = CGI::Emulate::PSGI->handler($sub);

	my $staticApp = Plack::App::MCCS->new(root => "./htdocs/webmysql")->to_app;
		
	my $builder = Plack::Builder->new();
	$builder->mount("/webmysql" => $staticApp);	
	$builder->mount("/" => $app);
	return $builder;
}
###############################################################################
return 1;
