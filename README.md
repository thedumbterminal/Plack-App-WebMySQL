# WebMySQL

Web based MySQL interface.

## Install

    perl Build.PL
    ./Build installdeps

## Usage

    plackup
    
## Customising

Any of the html files in the `cgi-bin/webmysql/templates` subdirectory may be modified. Please do not rename them or alter the comments in the page
as these are used as placeholders for the program. You may however move the location of the placeholders within the page.

You may also change the name of the webmysql program itself, this should be done in order to keep the program hidden from unwanted visitors.
    