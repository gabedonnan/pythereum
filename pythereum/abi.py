# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import json

from re import compile
from functools import partial
from eth_abi import encode
from eth_utils import function_signature_to_4byte_selector
from pythereum.exceptions import PythereumABIException
from pythereum.logs import logger


snake_case = compile(r"(?<!^)(?=[A-Z])")


class ContractABI:
    """
    Takes an ethereum contract ABI as input, and generates functions from it.
    This allows users to encode call data simply via abi_instance.abi_specified_function_name(abi_specified_args)
    """

    def __init__(self, data: list[dict] | str, to_snake_case: bool = True):
        if isinstance(data, str):
            data = json.loads(data)

        for func in data:
            if "name" in func:
                if to_snake_case:
                    setattr(
                        self,
                        snake_case.sub("_", func["name"]).lower(),
                        partial(self.encode_call, func["name"]),
                    )
                else:
                    setattr(
                        self, func["name"], partial(self.encode_call, func["name"])
                    )

        self._functions = {
            func["name"]: [(inp["name"], inp["type"]) for inp in func["inputs"]]
            for func in data
            if "name" in func
        }

        self.snake_case = to_snake_case

        self.logger = logger.getChild("ContractABI")

    def get_args(self, name: str) -> list[tuple]:
        """
        Gets the ABI argument names and types for a specified function.
        Will attempt to convert name from snake_case to PascalCase if it is not found
        :param name: The name of the function you would like to call
        :return: a list of tuples of form [(param_name, param_type), ...]
        """
        if name in self._functions:
            return self._functions[name]
        elif (
            pascal_name := name.replace("_", " ").title().replace(" ", "")
        ) in self._functions:
            return self._functions[pascal_name]

        raise PythereumABIException(
            f"Neither {name} nor {pascal_name} is defined in this ABI"
        )

    @property
    def stored_functions(self):
        """
        Gets a list of the stored function names
        """
        return list(self._functions.keys())

    def add_function(
        self,
        function_name: str,
        argument_types: list | tuple,
        argument_names: list | tuple | None = None,
    ) -> None:
        """
        Adds a new function to an ABI
        """
        if argument_names is None:
            self._functions[function_name] = [
                ("_", arg_type) for arg_type in argument_types
            ]
        else:
            self._functions[function_name] = list(zip(argument_names, argument_types))
         
        if self.snake_case:
            setattr(
                self,
                snake_case.sub("_", function_name).lower(),
                partial(self.encode_call, function_name),
            )
        else:
            setattr(self, function_name, partial(self.encode_call, function_name))

    def encode_call(self, name: str, *args) -> str:
        """
        Encodes an ABI call to a stored function with the specified arguments
        """
        required_args: list[tuple] = self._functions[name]

        if len(args) != len(required_args):
            raise PythereumABIException(
                f"Incorrect arguments, required arguments are {self.get_args(name)}", self.logger
            )

        arg_types = [arg[1] for arg in required_args]
        function_signature = name + "(" + ",".join(arg_types) + ")"
        return (
                "0x"
                + function_signature_to_4byte_selector(function_signature).hex()
                + encode(arg_types, args).hex()
        )


# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
