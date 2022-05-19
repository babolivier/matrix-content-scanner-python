# Copyright 2022 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import logging
from functools import cached_property

import twisted.internet.reactor
import yaml
from twisted.internet.interfaces import (
    IReactorCore,
    IReactorPluggableNameResolver,
    IReactorSSL,
    IReactorTCP,
    IReactorTime,
)
from twisted.python import log

from matrix_content_scanner.config import MatrixContentScannerConfig
from matrix_content_scanner.crypto import CryptoHandler
from matrix_content_scanner.httpserver import HTTPServer
from matrix_content_scanner.scanner.file_downloader import FileDownloader
from matrix_content_scanner.scanner.scanner import Scanner


class Reactor(
    IReactorCore,
    IReactorTCP,
    IReactorSSL,
    IReactorTime,
    IReactorPluggableNameResolver,
):
    pass


class MatrixContentScanner:
    def __init__(
        self,
        config: MatrixContentScannerConfig,
        reactor: Reactor = twisted.internet.reactor,  # type: ignore[assignment]
    ) -> None:
        self.config = config
        self.reactor = reactor

    @cached_property
    def file_downloader(self) -> FileDownloader:
        return FileDownloader(self)

    @cached_property
    def scanner(self) -> Scanner:
        return Scanner(self)

    @cached_property
    def crypto_handler(self) -> CryptoHandler:
        return CryptoHandler(self)

    def start(self) -> None:
        """Start the HTTP server and start the reactor."""
        setup_logging()
        http_server = HTTPServer(self)
        http_server.start()
        self.reactor.run()


def setup_logging() -> None:
    """Basic logging setup."""
    log_format = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(request_type)s - %(media_path)s - %(message)s"
    formatter = logging.Formatter(log_format)

    handler = logging.StreamHandler()

    handler.setFormatter(formatter)
    rootLogger = logging.getLogger("")
    rootLogger.setLevel("INFO")
    rootLogger.addHandler(handler)

    logging.getLogger("twisted").setLevel(logging.WARNING)

    observer = log.PythonLoggingObserver()
    observer.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A web service for scanning media hosted by a Matrix media repository."
    )
    parser.add_argument(
        "-c",
        type=argparse.FileType("r"),
        required=True,
        help="The YAML configuration file.",
    )

    args = parser.parse_args()
    cfg = MatrixContentScannerConfig(yaml.safe_load(args.c))

    mcs = MatrixContentScanner(cfg)
    mcs.start()
