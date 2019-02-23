GLSfetch
========

Basic example on how to download (new) documents from the German GLS Bank "Postbox" (Postkorb/Posteingang) using the BeautifulSoup scraper.

This should actually work for all banks that use the VR Volksbank Raiffeisenbank Online Banking system (but the example config contains the GLS info).

Usage
-----

1. Clone/download this repo.
2. Run `fetch.py` once and it will tell you where to store your configuration details. On Linux, it will most likely ask you to put them into `~/.local/share/glsfetch.ini`.
3. Copy `example.ini` there and change at least your username. If you don't want it to prompt for your password each time, you can also put your password there. Obviously, this might be unsafe, and you might want to think about file permissions and stuff.
4. Run `fetch.py`. If everything goes well, it will fetch all new/unread document attachments from your postbox and store them in the current directory.

Original source
---------------

[fetch.py](fetch.py) is an example on how to use a slightly modified version of the undocumented [VB-Scraper](https://github.com/andsor/VB-Scraper) "Scraping Tools for Volksbank Online Banking" library by [@andsor](https://github.com/andsor/).

Thanks Andreas!

License
-------

CC0-1.0 Creative Commons Zero, do what you want with it (but don't blame me). :-)
