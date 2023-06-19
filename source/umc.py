import argparse
import os
import time
from threading import Thread
from pathlib import Path

from . import conf, confwiz, fget, target

class NoConfigException(Exception): pass


class UMC():
    config: dict = None
    working_dir: Path = None

    __thread: Thread = None
    __halted: bool = False
    def __init__(self,wd: Path):
        if wd != None:
            self.working_dir = wd

    def halt(self):
        if self.__halted: pass
        pass
    
    def __load_conf(self, dir: str):
        self.config = conf.init_config(dir)
    
    def is_running(self):
        if self.__thread == None:
            return False
        
        return self.__thread.is_alive()

    def start(self):
        if self.is_running():
            raise Exception("Already running")
        
        if self.working_dir == None:
            raise Exception("aaaa no working dir")

        if self.config == None:
            c = self.__load_conf(self.working_dir)
            if c == None:
                raise NoConfigException("No config loaded")
        
        target.process_targets(
                    src_dir=self.working_dir,
                    all_files=[],
                    config=self.config
                    )