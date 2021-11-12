import argparse

class ArgParser:
    def __init__(self, desc : str, argsdict : "dict((type, str))"):
        self.parser = argparse.ArgumentParser(description=desc)
        for args in argsdict.keys():
            input_type, help_desc = argsdict[args]
            if input_type is None:
                self.parser.add_argument(args,
                        help=help_desc,
                        action="store_const",
                        const=True,
                        default=False)
            else:
                self.parser.add_argument(args,
                    help=help_desc,
                    type=input_type)

    def get_parsed_args(self) -> argparse.Namespace:
        return self.parser.parse_args()
