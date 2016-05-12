#!/usr/bin/env python
#

import sys
from cbapi.response.models import Feed, FeedAction
from cbapi.example_helpers import build_cli_parser, get_cb_response_object
from cbapi.errors import ServerError
import logging

log = logging.getLogger(__name__)


def list_feeds(cb, parser, args):
    for f in cb.select(Feed):
        print(f)
        print("")


def add_feed(cb, parser, args):
    configured_feeds = [f for f in cb.select(Feed) if f.feed_url == args.feed_url]
    if len(configured_feeds):
        print("Warning: Feeds already configured for this url: {0:s}:".format(args.feed_url))
        for f in configured_feeds:
            print(f)
            print("")
        if not args.force:
            return

    f = cb.create(Feed)
    f.feed_url = args.feed_url
    if args.enable:
        f.enable = True

    if args.username:
        f.username = args.username
    if args.password:
        f.password = args.password

    if args.cert:
        f.ssl_client_crt = open(args.cert, "rb").read()
    if args.key:
        f.ssl_client_key = open(args.key, "rb").read()

    if args.use_proxy:
        f.use_proxy = True

    if args.validate_server_cert:
        f.validate_server_cert = True

    log.debug("Adding feed: {0:s}".format(str(f)))

    try:
        f.save()
    except ServerError as se:
        if se.error_code == 500:
            print("Could not add feed:")
            print(" Received error code 500 from server. This is usually because the server cannot retrieve the feed.")
            print(" Check to ensure the Cb server has network connectivity and the credentials are correct.")
        else:
            print("Could not add feed: {0:s}".format(str(se)))
    except Exception as e:
        print("Could not add feed: {0:s}".format(str(e)))
    else:
        log.debug("Feed data: {0:s}".format(str(f)))
        print("Added feed. New feed ID is {0:d}".format(f.id))


def delete_feed(cb, parser, args):
    try:
        if args.id:
            attempted_to_find = "ID of {0:d}".format(args.id)
            feeds = [cb.select(Feed, args.id, force_init=True)]
        else:
            attempted_to_find = "name {0:s}".format(args.feedname)
            feeds = cb.select(Feed).where("name:{0:s}".format(args.feedname))[::]
            if not len(feeds):
                raise Exception("No feeds match")
    except Exception as e:
        print("Could not find feed with {0:s}: {1:s}".format(attempted_to_find, str(e)))
        return

    num_matching_feeds = len(feeds)
    if num_matching_feeds > 1 and not args.force:
        print("{0:d} feeds match {1:s} and --force not specified. No action taken.".format(num_matching_feeds,
                                                                                           attempted_to_find))
        return

    for f in feeds:
        try:
            f.delete()
        except Exception as e:
            print("Could not delete feed with {0:s}: {1:s}".format(attempted_to_find, str(e)))
        else:
            print("Deleted feed id {0:d} with name {1:s}".format(f.id, f.name))


def main():
    parser = build_cli_parser()
    commands = parser.add_subparsers(help="Feed commands", dest="command_name")

    list_command = commands.add_parser("list", help="List all configured feeds")

    add_command = commands.add_parser("add", help="Add new feed")
    add_command.add_argument("-u", "--feed-url", help="URL location of feed data", dest="feed_url", required=True)
    add_command.add_argument("--force", help="Force creation even if feed already exists", action="store_true")
    add_command.add_argument("-e", "--enable", action="store_true", help="Enable this feed")
    add_command.add_argument("-p", "--use_proxy", action="store_true", default=False, dest="use_proxy",
                             help="Carbon Black server will use configured web proxy to download feed from feed url")
    add_command.add_argument("-v", "--validate_server_cert", action="store_true", default=False,
                             dest="validate_server_cert",
                             help="Carbon Black server will verify the SSL certificate of the feed server")
    http_basic_auth = add_command.add_argument_group("HTTP Authentication")
    http_basic_auth.add_argument("--username", help="HTTP Basic Authentication username to access Feed URL")
    http_basic_auth.add_argument("--password", help="HTTP Basic Authentication password to access Feed URL")
    tls_auth = add_command.add_argument_group("TLS Client Authentication")
    tls_auth.add_argument("--cert",
                          help="Path to file containing TLS client certificate required to access Feed URL")
    tls_auth.add_argument("--key", help="Path to file containing TLS client key required to access Feed URL")

    del_command = commands.add_parser("delete", help="Delete feeds")
    del_feed_specifier = del_command.add_mutually_exclusive_group(required=True)
    del_feed_specifier.add_argument("-i", "--id", type=int, help="ID of feed to delete")
    del_feed_specifier.add_argument("-f", "--feedname", help="Name of feed to delete. Specify --force to delete"
                                    " multiple feeds that have the same name")
    del_command.add_argument("--force", help="If FEEDNAME matches multiple feeds, delete all matching feeds",
                             action="store_true", default=False)

    args = parser.parse_args()
    cb = get_cb_response_object(args)

    if args.command_name == "list":
        return list_feeds(cb, parser, args)
    elif args.command_name == "add":
        return add_feed(cb, parser, args)
    elif args.command_name == "delete":
        return delete_feed(cb, parser, args)


if __name__ == "__main__":
    sys.exit(main())
