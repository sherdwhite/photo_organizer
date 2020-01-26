#!/usr/bin/env python
from gevent import monkey

monkey.patch_all(thread=False)

if __name__ == "__main__":
    from photo_organizer import main

    main.run()
