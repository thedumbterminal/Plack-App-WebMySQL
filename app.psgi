use strict;
use warnings;
use CGI::Compile;
use CGI::Emulate::PSGI;
use Plack::Builder;
use Plack::App::MCCS;
use lib "lib";

my $sub = CGI::Compile->compile("./cgi-bin/webmysql/webmysql.cgi");
my $app = CGI::Emulate::PSGI->handler($sub);

my $staticApp = Plack::App::MCCS->new(root => "./htdocs/webmysql")->to_app;
builder {
	mount "/webmysql" => $staticApp;	
	mount "/" => $app;
};
