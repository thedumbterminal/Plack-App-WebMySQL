# Plack::App::WebMySQL

[![Build Status](https://travis-ci.org/thedumbterminal/Plack-App-WebMySQL.svg?branch=master)](https://travis-ci.org/thedumbterminal/Plack-App-WebMySQL)

Web based MySQL interface.

## Install

### Environment

Run MariaDb:

    docker run --detach --env MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 -p 3306:3306 mariadb:latest

Install MariaDB client libraries:

    brew install mariadb

Configure perl:

    plenv install `cat .perl-version`
    plenv local
    plenv install-cpanm
    cpanm local::lib Module::Build::Pluggable::CPANfile

### App

Install:

    perl Build.PL
    ./Build installdeps --cpan_client 'cpanm --notest'

Run tests:

    ./Build test

## Usage

As a module:

    use Plack::App::WebMySQL;
    my $app = Plack::App::WebMySQL->new()->to_app;

Standalone:

    plackup

Then browse to [http://localhost:5000/app](http://localhost:5000/)

## Customising

Any of the html files in the `cgi-bin/webmysql/templates` subdirectory may be modified. Please do not rename them or alter the comments in the page
as these are used as placeholders for the program. You may however move the location of the placeholders within the page.

You may also change the name of the webmysql program itself, this should be done in order to keep the program hidden from unwanted visitors.

## Running on Heroku

Only setting the correct buildpack is required:

    heroku config:set BUILDPACK_URL=https://github.com/miyagawa/heroku-buildpack-perl --app yourappname
