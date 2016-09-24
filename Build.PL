use strict;
use warnings;
use Module::Build::Pluggable (
    'CPANfile'
);
my $build = Module::Build::Pluggable->new(
	module_name => 'Plack::App::WebMySQL',
	license => 'restrictive',
	dist_author => 'MacGyveR <dumb@cpan.org>',
	dist_abstract => 'WebMySQL web application',
	create_makefile_pl => 'traditional'
);
$build->create_build_script;
