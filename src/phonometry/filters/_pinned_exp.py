#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""``exp`` and ``pow``, spelled in arithmetic IEEE 754 pins.

:mod:`phonometry.filters._weighting_design` takes an exponential inside every
Levenberg-Marquardt step and a power in every Lawson round, on the frequency
grid and once more for the shipped gain. Taken from :mod:`math`, each of those
is whatever routine the platform's C library ships, and the C libraries do not
agree to the last bit: glibc, Apple's libm and the Windows runtime each round
a fraction of inputs to the other neighbour, and the fit amplifies a last bit
into a different filter. This module removes the platform from the result. It
spells the routines glibc ships for ``exp`` and ``pow`` (ARM's
optimized-routines, ``math/exp.c`` and ``math/pow.c``, which glibc has carried
since 2.29) in numpy array arithmetic that IEEE 754 fixes exactly, so the
answer is a function of the input alone.

The C routines are compiled, on every x86-64 machine with a fused multiply-add
unit, into a variant where the compiler fuses most multiply-adds; that variant
is the one the Linux digest of the weighting design was measured on, and it is
the one spelled here. Which operations it fuses was read off the shipped
binary's own instructions (glibc 2.41, ``__exp_fma`` and ``__pow_fma``), and
each fused site is reproduced by :func:`_fused_multiply_add`, an exact
emulation: the product and the first sum are made exact, the last two parts are
added with rounding to odd, and the final rounding then lands where a single
fused operation lands (Boldo and Melquiond, "Emulation of FMA and correctly
rounded sums: proved algorithms using rounding to odd", IEEE Transactions on
Computers 57(4), 2008). It is correctly rounded for every operand triple whose
product neither overflows nor loses bits to the subnormal range, which every
call site here satisfies.

What "the routine glibc ships" rests on is measured, not asserted:
``tests/filters/test_pinned_exp.py`` holds both functions bit for bit to
:func:`math.exp` and :func:`math.pow` on a machine whose C library is that
routine, over the inputs an actual design evaluates and over draws spanning the
full domain, and to :func:`math.fma` for the emulation.

The tables and polynomial coefficients are copied digit for digit from ARM's
optimized-routines (``math/exp_data.c`` and ``math/pow_log_data.c``), which glibc
carries verbatim as ``e_exp_data.c`` and ``e_pow_log_data.c`` for this
configuration (``EXP_TABLE_BITS == 7``, ``EXP_POLY_ORDER == 5``,
``POW_LOG_TABLE_BITS == 7``, ``POW_LOG_POLY_ORDER == 8``).
"""

from __future__ import annotations

import numpy as np

from .._internal.validation import real_array
from ._pinned_log import _two_product

__all__ = ["pinned_exp", "pinned_pow"]

# The tables and polynomial constants below are copied from ARM's
# optimized-routines, math/exp_data.c and math/pow_log_data.c, and are
# redistributed under that project's MIT license, whose notice the license
# requires to travel with them:
#
#   Copyright (c) 2018-2023, Arm Limited.
#
#   Permission is hereby granted, free of charge, to any person obtaining
#   a copy of this software and associated documentation files (the
#   "Software"), to deal in the Software without restriction, including
#   without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to
#   permit persons to whom the Software is furnished to do so, subject to
#   the following conditions:
#
#   The above copyright notice and this permission notice shall be included
#   in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#   OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#   SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#: ``exp_data.tab``: for ``k`` in ``[0, 128)``, the bit pattern of the tail
#: ``T[k]`` and of ``H[k]`` less ``k << 45``, where ``2^(k/128)`` is
#: ``H[k] * (1 + T[k])``. Four words a row.
_EXP_TAB_HEX = (
    "0000000000000000 3ff0000000000000 3c9b3b4f1a88bf6e 3feff63da9fb3335",
    "bc7160139cd8dc5d 3fefec9a3e778061 bc905e7a108766d1 3fefe315e86e7f85",
    "3c8cd2523567f613 3fefd9b0d3158574 bc8bce8023f98efa 3fefd06b29ddf6de",
    "3c60f74e61e6c861 3fefc74518759bc8 3c90a3e45b33d399 3fefbe3ecac6f383",
    "3c979aa65d837b6d 3fefb5586cf9890f 3c8eb51a92fdeffc 3fefac922b7247f7",
    "3c3ebe3d702f9cd1 3fefa3ec32d3d1a2 bc6a033489906e0b 3fef9b66affed31b",
    "bc9556522a2fbd0e 3fef9301d0125b51 bc5080ef8c4eea55 3fef8abdc06c31cc",
    "bc91c923b9d5f416 3fef829aaea92de0 3c80d3e3e95c55af 3fef7a98c8a58e51",
    "bc801b15eaa59348 3fef72b83c7d517b bc8f1ff055de323d 3fef6af9388c8dea",
    "3c8b898c3f1353bf 3fef635beb6fcb75 bc96d99c7611eb26 3fef5be084045cd4",
    "3c9aecf73e3a2f60 3fef54873168b9aa bc8fe782cb86389d 3fef4d5022fcd91d",
    "3c8a6f4144a6c38d 3fef463b88628cd6 3c807a05b0e4047d 3fef3f49917ddc96",
    "3c968efde3a8a894 3fef387a6e756238 3c875e18f274487d 3fef31ce4fb2a63f",
    "3c80472b981fe7f2 3fef2b4565e27cdd bc96b87b3f71085e 3fef24dfe1f56381",
    "3c82f7e16d09ab31 3fef1e9df51fdee1 bc3d219b1a6fbffa 3fef187fd0dad990",
    "3c8b3782720c0ab4 3fef1285a6e4030b 3c6e149289cecb8f 3fef0cafa93e2f56",
    "3c834d754db0abb6 3fef06fe0a31b715 3c864201e2ac744c 3fef0170fc4cd831",
    "3c8fdd395dd3f84a 3feefc08b26416ff bc86a3803b8e5b04 3feef6c55f929ff1",
    "bc924aedcc4b5068 3feef1a7373aa9cb bc9907f81b512d8e 3feeecae6d05d866",
    "bc71d1e83e9436d2 3feee7db34e59ff7 bc991919b3ce1b15 3feee32dc313a8e5",
    "3c859f48a72a4c6d 3feedea64c123422 bc9312607a28698a 3feeda4504ac801c",
    "bc58a78f4817895b 3feed60a21f72e2a bc7c2c9b67499a1b 3feed1f5d950a897",
    "3c4363ed60c2ac11 3feece086061892d 3c9666093b0664ef 3feeca41ed1d0057",
    "3c6ecce1daa10379 3feec6a2b5c13cd0 3c93ff8e3f0f1230 3feec32af0d7d3de",
    "3c7690cebb7aafb0 3feebfdad5362a27 3c931dbdeb54e077 3feebcb299fddd0d",
    "bc8f94340071a38e 3feeb9b2769d2ca7 bc87deccdc93a349 3feeb6daa2cf6642",
    "bc78dec6bd0f385f 3feeb42b569d4f82 bc861246ec7b5cf6 3feeb1a4ca5d920f",
    "3c93350518fdd78e 3feeaf4736b527da 3c7b98b72f8a9b05 3feead12d497c7fd",
    "3c9063e1e21c5409 3feeab07dd485429 3c34c7855019c6ea 3feea9268a5946b7",
    "3c9432e62b64c035 3feea76f15ad2148 bc8ce44a6199769f 3feea5e1b976dc09",
    "bc8c33c53bef4da8 3feea47eb03a5585 bc845378892be9ae 3feea34634ccc320",
    "bc93cedd78565858 3feea23882552225 3c5710aa807e1964 3feea155d44ca973",
    "bc93b3efbf5e2228 3feea09e667f3bcd bc6a12ad8734b982 3feea012750bdabf",
    "bc6367efb86da9ee 3fee9fb23c651a2f bc80dc3d54e08851 3fee9f7df9519484",
    "bc781f647e5a3ecf 3fee9f75e8ec5f74 bc86ee4ac08b7db0 3fee9f9a48a58174",
    "bc8619321e55e68a 3fee9feb564267c9 3c909ccb5e09d4d3 3feea0694fde5d3f",
    "bc7b32dcb94da51d 3feea11473eb0187 3c94ecfd5467c06b 3feea1ed0130c132",
    "3c65ebe1abd66c55 3feea2f336cf4e62 bc88a1c52fb3cf42 3feea427543e1a12",
    "bc9369b6f13b3734 3feea589994cce13 bc805e843a19ff1e 3feea71a4623c7ad",
    "bc94d450d872576e 3feea8d99b4492ed 3c90ad675b0e8a00 3feeaac7d98a6699",
    "3c8db72fc1f0eab4 3feeace5422aa0db bc65b6609cc5e7ff 3feeaf3216b5448c",
    "3c7bf68359f35f44 3feeb1ae99157736 bc93091fa71e3d83 3feeb45b0b91ffc6",
    "bc5da9b88b6c1e29 3feeb737b0cdc5e5 bc6c23f97c90b959 3feeba44cbc8520f",
    "bc92434322f4f9aa 3feebd829fde4e50 bc85ca6cd7668e4b 3feec0f170ca07ba",
    "3c71affc2b91ce27 3feec49182a3f090 3c6dd235e10a73bb 3feec86319e32323",
    "bc87c50422622263 3feecc667b5de565 3c8b1c86e3e231d5 3feed09bec4a2d33",
    "bc91bbd1d3bcbb15 3feed503b23e255d 3c90cc319cee31d2 3feed99e1330b358",
    "3c8469846e735ab3 3feede6b5579fdbf bc82dfcd978e9db4 3feee36bbfd3f37a",
    "3c8c1a7792cb3387 3feee89f995ad3ad bc907b8f4ad1d9fa 3feeee07298db666",
    "bc55c3d956dcaeba 3feef3a2b84f15fb bc90a40e3da6f640 3feef9728de5593a",
    "bc68d6f438ad9334 3feeff76f2fb5e47 bc91eee26b588a35 3fef05b030a1064a",
    "3c74ffd70a5fddcd 3fef0c1e904bc1d2 bc91bdfbfa9298ac 3fef12c25bd71e09",
    "3c736eae30af0cb3 3fef199bdd85529c 3c8ee3325c9ffd94 3fef20ab5fffd07a",
    "3c84e08fd10959ac 3fef27f12e57d14b 3c63cdaf384e1a67 3fef2f6d9406e7b5",
    "3c676b2c6c921968 3fef3720dcef9069 bc808a1883ccb5d2 3fef3f0b555dc3fa",
    "bc8fad5d3ffffa6f 3fef472d4a07897c bc900dae3875a949 3fef4f87080d89f2",
    "3c74a385a63d07a7 3fef5818dcfba487 bc82919e2040220f 3fef60e316c98398",
    "3c8e5a50d5c192ac 3fef69e603db3285 3c843a59ac016b4b 3fef7321f301b460",
    "bc82d52107b43e1f 3fef7c97337b9b5f bc892ab93b470dc9 3fef864614f5a129",
    "3c74b604603a88d3 3fef902ee78b3ff6 3c83c5ec519d7271 3fef9a51fbc74c83",
    "bc8ff7128fd391f0 3fefa4afa2a490da bc8dae98e223747d 3fefaf482d8e67f1",
    "3c8ec3bc41aa2008 3fefba1bee615a27 3c842b94c3a9eb32 3fefc52b376bba97",
    "3c8a64a931d185ee 3fefd0765b6e4540 bc8e37bae43be3ed 3fefdbfdad9cbe14",
    "3c77893b4d91cd9d 3fefe7c1819e90d8 3c5305c14160cc89 3feff3c22b8f71f1",
)

#: ``pow_log_data.tab``: for each of the 128 subintervals, the bit patterns of
#: ``invc``, ``logc`` and ``logctail`` (the C table's unused padding word is
#: dropped).
_POW_TAB_HEX = (
    "3ff6a00000000000 bfd62c82f2b9c800 3cfab42428375680",
    "3ff6800000000000 bfd5d1bdbf580800 bd1ca508d8e0f720",
    "3ff6600000000000 bfd5767717455800 bd2362a4d5b6506d",
    "3ff6400000000000 bfd51aad872df800 bce684e49eb067d5",
    "3ff6200000000000 bfd4be5f95777800 bd041b6993293ee0",
    "3ff6000000000000 bfd4618bc21c6000 3d13d82f484c84cc",
    "3ff5e00000000000 bfd404308686a800 3cdc42f3ed820b3a",
    "3ff5c00000000000 bfd3a64c55694800 3d20b1c686519460",
    "3ff5a00000000000 bfd347dd9a988000 3d25594dd4c58092",
    "3ff5800000000000 bfd2e8e2bae12000 3d267b1e99b72bd8",
    "3ff5600000000000 bfd2895a13de8800 3d15ca14b6cfb03f",
    "3ff5600000000000 bfd2895a13de8800 3d15ca14b6cfb03f",
    "3ff5400000000000 bfd22941fbcf7800 bd165a242853da76",
    "3ff5200000000000 bfd1c898c1699800 bd1fafbc68e75404",
    "3ff5000000000000 bfd1675cababa800 3d1f1fc63382a8f0",
    "3ff4e00000000000 bfd1058bf9ae4800 bd26a8c4fd055a66",
    "3ff4c00000000000 bfd0a324e2739000 bd0c6bee7ef4030e",
    "3ff4a00000000000 bfd0402594b4d000 bcf036b89ef42d7f",
    "3ff4a00000000000 bfd0402594b4d000 bcf036b89ef42d7f",
    "3ff4800000000000 bfcfb9186d5e4000 3d0d572aab993c87",
    "3ff4600000000000 bfcef0adcbdc6000 3d2b26b79c86af24",
    "3ff4400000000000 bfce27076e2af000 bd172f4f543fff10",
    "3ff4200000000000 bfcd5c216b4fc000 3d21ba91bbca681b",
    "3ff4000000000000 bfcc8ff7c79aa000 3d27794f689f8434",
    "3ff4000000000000 bfcc8ff7c79aa000 3d27794f689f8434",
    "3ff3e00000000000 bfcbc286742d9000 3d194eb0318bb78f",
    "3ff3c00000000000 bfcaf3c94e80c000 3cba4e633fcd9066",
    "3ff3a00000000000 bfca23bc1fe2b000 bd258c64dc46c1ea",
    "3ff3a00000000000 bfca23bc1fe2b000 bd258c64dc46c1ea",
    "3ff3800000000000 bfc9525a9cf45000 bd2ad1d904c1d4e3",
    "3ff3600000000000 bfc87fa06520d000 3d2bbdbf7fdbfa09",
    "3ff3400000000000 bfc7ab890210e000 3d2bdb9072534a58",
    "3ff3400000000000 bfc7ab890210e000 3d2bdb9072534a58",
    "3ff3200000000000 bfc6d60fe719d000 bd10e46aa3b2e266",
    "3ff3000000000000 bfc5ff3070a79000 bd1e9e439f105039",
    "3ff3000000000000 bfc5ff3070a79000 bd1e9e439f105039",
    "3ff2e00000000000 bfc526e5e3a1b000 bd20de8b90075b8f",
    "3ff2c00000000000 bfc44d2b6ccb8000 3d170cc16135783c",
    "3ff2c00000000000 bfc44d2b6ccb8000 3d170cc16135783c",
    "3ff2a00000000000 bfc371fc201e9000 3cf178864d27543a",
    "3ff2800000000000 bfc29552f81ff000 bd248d301771c408",
    "3ff2600000000000 bfc1b72ad52f6000 bd2e80a41811a396",
    "3ff2600000000000 bfc1b72ad52f6000 bd2e80a41811a396",
    "3ff2400000000000 bfc0d77e7cd09000 3d0a699688e85bf4",
    "3ff2400000000000 bfc0d77e7cd09000 3d0a699688e85bf4",
    "3ff2200000000000 bfbfec9131dbe000 bd2575545ca333f2",
    "3ff2000000000000 bfbe27076e2b0000 3d2a342c2af0003c",
    "3ff2000000000000 bfbe27076e2b0000 3d2a342c2af0003c",
    "3ff1e00000000000 bfbc5e548f5bc000 bd1d0c57585fbe06",
    "3ff1c00000000000 bfba926d3a4ae000 3d253935e85baac8",
    "3ff1c00000000000 bfba926d3a4ae000 3d253935e85baac8",
    "3ff1a00000000000 bfb8c345d631a000 3d137c294d2f5668",
    "3ff1a00000000000 bfb8c345d631a000 3d137c294d2f5668",
    "3ff1800000000000 bfb6f0d28ae56000 bd269737c93373da",
    "3ff1600000000000 bfb51b073f062000 3d1f025b61c65e57",
    "3ff1600000000000 bfb51b073f062000 3d1f025b61c65e57",
    "3ff1400000000000 bfb341d7961be000 3d2c5edaccf913df",
    "3ff1400000000000 bfb341d7961be000 3d2c5edaccf913df",
    "3ff1200000000000 bfb16536eea38000 3d147c5e768fa309",
    "3ff1000000000000 bfaf0a30c0118000 3d2d599e83368e91",
    "3ff1000000000000 bfaf0a30c0118000 3d2d599e83368e91",
    "3ff0e00000000000 bfab42dd71198000 3d1c827ae5d6704c",
    "3ff0e00000000000 bfab42dd71198000 3d1c827ae5d6704c",
    "3ff0c00000000000 bfa77458f632c000 bd2cfc4634f2a1ee",
    "3ff0c00000000000 bfa77458f632c000 bd2cfc4634f2a1ee",
    "3ff0a00000000000 bfa39e87b9fec000 3cf502b7f526feaa",
    "3ff0a00000000000 bfa39e87b9fec000 3cf502b7f526feaa",
    "3ff0800000000000 bf9f829b0e780000 bd2980267c7e09e4",
    "3ff0800000000000 bf9f829b0e780000 bd2980267c7e09e4",
    "3ff0600000000000 bf97b91b07d58000 bd288d5493faa639",
    "3ff0400000000000 bf8fc0a8b0fc0000 bcdf1e7cf6d3a69c",
    "3ff0400000000000 bf8fc0a8b0fc0000 bcdf1e7cf6d3a69c",
    "3ff0200000000000 bf7fe02a6b100000 bd19e23f0dda40e4",
    "3ff0200000000000 bf7fe02a6b100000 bd19e23f0dda40e4",
    "3ff0000000000000 0000000000000000 0000000000000000",
    "3ff0000000000000 0000000000000000 0000000000000000",
    "3fefc00000000000 3f80101575890000 bd10c76b999d2be8",
    "3fef800000000000 3f90205658938000 bd23dc5b06e2f7d2",
    "3fef400000000000 3f98492528c90000 bd2aa0ba325a0c34",
    "3fef000000000000 3fa0415d89e74000 3d0111c05cf1d753",
    "3feec00000000000 3fa466aed42e0000 bd2c167375bdfd28",
    "3fee800000000000 3fa894aa149fc000 bd197995d05a267d",
    "3fee400000000000 3faccb73cdddc000 bd1a68f247d82807",
    "3fee200000000000 3faeea31c006c000 bd0e113e4fc93b7b",
    "3fede00000000000 3fb1973bd1466000 bd25325d560d9e9b",
    "3feda00000000000 3fb3bdf5a7d1e000 3d2cc85ea5db4ed7",
    "3fed600000000000 3fb5e95a4d97a000 bd2c69063c5d1d1e",
    "3fed400000000000 3fb700d30aeac000 3cec1e8da99ded32",
    "3fed000000000000 3fb9335e5d594000 3d23115c3abd47da",
    "3fecc00000000000 3fbb6ac88dad6000 bd1390802bf768e5",
    "3feca00000000000 3fbc885801bc4000 3d2646d1c65aacd3",
    "3fec600000000000 3fbec739830a2000 bd2dc068afe645e0",
    "3fec400000000000 3fbfe89139dbe000 bd2534d64fa10afd",
    "3fec000000000000 3fc1178e8227e000 3d21ef78ce2d07f2",
    "3febe00000000000 3fc1aa2b7e23f000 3d2ca78e44389934",
    "3feba00000000000 3fc2d1610c868000 3d039d6ccb81b4a1",
    "3feb800000000000 3fc365fcb0159000 3cc62fa8234b7289",
    "3feb400000000000 3fc4913d8333b000 3d25837954fdb678",
    "3feb200000000000 3fc527e5e4a1b000 3d2633e8e5697dc7",
    "3feae00000000000 3fc6574ebe8c1000 3d19cf8b2c3c2e78",
    "3feac00000000000 3fc6f0128b757000 bd25118de59c21e1",
    "3feaa00000000000 3fc7898d85445000 bd1c661070914305",
    "3fea600000000000 3fc8beafeb390000 bd073d54aae92cd1",
    "3fea400000000000 3fc95a5adcf70000 3d07f22858a0ff6f",
    "3fea000000000000 3fca93ed3c8ae000 bd28724350562169",
    "3fe9e00000000000 3fcb31d8575bd000 bd0c358d4eace1aa",
    "3fe9c00000000000 3fcbd087383be000 bd2d4bc4595412b6",
    "3fe9a00000000000 3fcc6ffbc6f01000 bcf1ec72c5962bd2",
    "3fe9600000000000 3fcdb13db0d49000 bd2aff2af715b035",
    "3fe9400000000000 3fce530effe71000 3cc212276041f430",
    "3fe9200000000000 3fcef5ade4dd0000 bcca211565bb8e11",
    "3fe9000000000000 3fcf991c6cb3b000 3d1bcbecca0cdf30",
    "3fe8c00000000000 3fd07138604d5800 3cf89cdb16ed4e91",
    "3fe8a00000000000 3fd0c42d67616000 3d27188b163ceae9",
    "3fe8800000000000 3fd1178e8227e800 bd2c210e63a5f01c",
    "3fe8600000000000 3fd16b5ccbacf800 3d2b9acdf7a51681",
    "3fe8400000000000 3fd1bf99635a6800 3d2ca6ed5147bdb7",
    "3fe8200000000000 3fd214456d0eb800 3d0a87deba46baea",
    "3fe7e00000000000 3fd2bef07cdc9000 3d2a9cfa4a5004f4",
    "3fe7c00000000000 3fd314f1e1d36000 bd28e27ad3213cb8",
    "3fe7a00000000000 3fd36b6776be1000 3d116ecdb0f177c8",
    "3fe7800000000000 3fd3c25277333000 3d183b54b606bd5c",
    "3fe7600000000000 3fd419b423d5e800 3d08e436ec90e09d",
    "3fe7400000000000 3fd4718dc271c800 bd2f27ce0967d675",
    "3fe7200000000000 3fd4c9e09e173000 bd2e20891b0ad8a4",
    "3fe7000000000000 3fd522ae0738a000 3d2ebe708164c759",
    "3fe6e00000000000 3fd57bf753c8d000 3d1fadedee5d40ef",
    "3fe6c00000000000 3fd5d5bddf596000 bd0a0b2a08a465dc",
)

_EXP_TAB = np.array(
    [int(word, 16) for row in _EXP_TAB_HEX for word in row.split()], dtype=np.uint64
)
_EXP_TAIL = _EXP_TAB[0::2].view(np.float64)
_EXP_SBITS = _EXP_TAB[1::2].copy()

_POW_TAB = (
    np.array(
        [int(word, 16) for row in _POW_TAB_HEX for word in row.split()],
        dtype=np.uint64,
    )
    .view(np.float64)
    .reshape(128, 3)
)
_POW_INVC = _POW_TAB[:, 0].copy()
_POW_LOGC = _POW_TAB[:, 1].copy()
_POW_LOGCTAIL = _POW_TAB[:, 2].copy()

#: ``exp_data``: ``N / ln 2``, ``-ln 2 / N`` split high and low, the rounding
#: shift ``0x1.8p52`` and the four polynomial coefficients ``C2..C5``.
_INV_LN2_N = float.fromhex("0x1.71547652b82fep0") * 128.0
_NEG_LN2_HI_N = float.fromhex("-0x1.62e42fefa0000p-8")
_NEG_LN2_LO_N = float.fromhex("-0x1.cf79abc9e3b3ap-47")
_SHIFT = float.fromhex("0x1.8p52")
_C2 = float.fromhex("0x1.ffffffffffdbdp-2")
_C3 = float.fromhex("0x1.555555555543cp-3")
_C4 = float.fromhex("0x1.55555cf172b91p-5")
_C5 = float.fromhex("0x1.1111167a4d017p-7")

#: ``pow_log_data``: ``ln 2`` split high and low, and the polynomial
#: ``A[0..6]`` with the scaling the C file applies (every factor a power of
#: two, so each product is exact).
_LN2_HI = float.fromhex("0x1.62e42fefa3800p-1")
_LN2_LO = float.fromhex("0x1.ef35793c76730p-45")
_A = (
    float.fromhex("-0x1p-1"),
    float.fromhex("0x1.555555555556p-2") * -2.0,
    float.fromhex("-0x1.0000000000006p-2") * -2.0,
    float.fromhex("0x1.999999959554ep-3") * 4.0,
    float.fromhex("-0x1.555555529a47ap-3") * 4.0,
    float.fromhex("0x1.2495b9b4845e9p-3") * -8.0,
    float.fromhex("-0x1.0002b8b263fc3p-3") * -8.0,
)

#: ``x = 2^k z`` decomposition offset of ``pow``'s logarithm: ``z`` lands in
#: ``[0x1.69555p-1, 0x1.69555p0)``.
_POW_OFF = np.uint64(0x3FE6955500000000)

#: Exponent fields that bound ``exp``'s fast path: ``2^-54``, ``512`` and
#: ``1024``.
_TOP_TINY = 0x3C9
_TOP_LARGE = 0x408
_TOP_HUGE = 0x409

#: Exponent fields that bound ``pow``'s main path in the exponent: ``2^-65``
#: and ``2^63``. Beyond them the power is ``1 +- y`` or overflows outright.
_TOP_Y_TINY = 0x3BE
_TOP_Y_HUGE = 0x43E

#: Veltkamp's splitting constant, ``2**27 + 1``.
_SPLIT = 134217729.0

_U1 = np.uint64(1)
_U45 = np.uint64(45)
_U52 = np.uint64(52)
_EXPONENT = np.uint64(0x7FF)
_MASK_127 = np.uint64(127)
_MINUS_ONE = np.uint64(0xFFFFFFFFFFFFFFFF)
_SIGN = np.uint64(0x8000000000000000)
#: Every bit of a double but its sign: zero exactly on +0.0 and -0.0.
_MAGNITUDE = np.uint64(0x7FFFFFFFFFFFFFFF)


def _split(value: float) -> tuple[float, float]:
    """Veltkamp's split of a constant: high and low halves of 26 bits or fewer."""
    scaled = value * _SPLIT
    high = scaled - (scaled - value)
    return high, value - high


def _top(values: np.ndarray) -> np.ndarray:
    """The exponent field of each double, as a signed integer."""
    return ((values.view(np.uint64) >> _U52) & _EXPONENT).astype(np.int64)


def _round_to_odd_sum(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """``a + b`` rounded to odd: the exact sum if it is a double, else the odd neighbour.

    The rounding Boldo and Melquiond's emulation needs. The sum is rounded to
    nearest and its error made exact (Knuth's two-sum); where the sum was
    inexact and came out even, the neighbour on the error's side is odd, and
    it is the one bracketing the exact value, so one step of a unit in the last
    place toward the error gives the round-to-odd result.

    :param a: First addend.
    :param b: Second addend.
    :return: The sum, rounded to odd.
    """
    total = np.asarray(a + b, dtype=np.float64)
    back = total - a
    error = (a - (total - back)) + (b - back)
    bits = total.view(np.uint64)
    # Read off the bits, as the parity is: the sum was inexact exactly where
    # its error has a magnitude bit set, whatever the error's sign.
    inexact = (error.view(np.uint64) & _MAGNITUDE) != 0
    inexact_even = inexact & ((bits & _U1) == 0)
    if not inexact_even.any():
        return total
    away = np.signbit(error) == np.signbit(total)
    step = np.where(away, _U1, _MINUS_ONE)
    return np.asarray(np.where(inexact_even, (bits + step).view(np.float64), total))


def _fused_multiply_add(
    a: np.ndarray, b: np.ndarray | float, c: np.ndarray | float
) -> np.ndarray:
    """``fl(a * b + c)`` with a single rounding, in plain IEEE 754 operations.

    The product is split exactly (Dekker's two-product), the addend joins its
    high part exactly (Knuth's two-sum), the two low parts are added rounded to
    odd and the final sum is rounded to nearest. Rounding to odd keeps what a
    double rounding would lose, so the last step lands on the fused result:
    proved for binary64 by Boldo and Melquiond (2008) whenever no step
    overflows and the product's error term is not subnormal.

    :param a: First factor, an array.
    :param b: Second factor.
    :param c: Addend.
    :return: The fused multiply-add, correctly rounded once.
    """
    product, product_error = _two_product(a, real_array(b, "b"))
    high = c + product
    back = high - c
    low = (c - (high - back)) + (product - back)
    return np.asarray(high + _round_to_odd_sum(low, product_error))


def _fused_by_constant(
    a: np.ndarray, constant: float, halves: tuple[float, float], c: np.ndarray | float
) -> np.ndarray:
    """:func:`_fused_multiply_add` with a constant factor split once, in advance."""
    product = a * constant
    scaled = a * _SPLIT
    a_high = scaled - (scaled - a)
    a_low = a - a_high
    high_c, low_c = halves
    product_error = (
        (a_high * high_c - product) + a_high * low_c + a_low * high_c
    ) + a_low * low_c
    high = c + product
    back = high - c
    low = (c - (high - back)) + (product - back)
    return np.asarray(high + _round_to_odd_sum(low, product_error))


_INV_LN2_N_HALVES = _split(_INV_LN2_N)
_NEG_LN2_HI_N_HALVES = _split(_NEG_LN2_HI_N)
_NEG_LN2_LO_N_HALVES = _split(_NEG_LN2_LO_N)
_C3_HALVES = _split(_C3)
_C5_HALVES = _split(_C5)


def _exp_kernel(
    x: np.ndarray, tail: np.ndarray | None, sign_bias: int = 0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The shared table step of ``exp`` and ``pow``: ``tmp``, ``sbits`` and ``ki``.

    ``exp(x) = 2^(k/N) exp(r)`` with ``x = k ln2/N + r``. Every multiply-add
    the shipped binary fuses is fused here; the rest are plain operations in
    the order the binary performs them.

    :param x: Arguments with ``2^-54 <= |x| < 1024``.
    :param tail: The low part of ``y log x`` that ``pow`` adds to ``r``, or
        ``None`` for ``exp``, which adds nothing.
    :param sign_bias: ``pow``'s sign bias, added to ``k`` before it becomes
        the exponent.
    :return: ``(tmp, sbits, ki)`` as the C routine names them.
    """
    shifted = _fused_by_constant(x, _INV_LN2_N, _INV_LN2_N_HALVES, _SHIFT)
    ki = shifted.view(np.uint64)
    kd = shifted - _SHIFT
    r = _fused_by_constant(kd, _NEG_LN2_HI_N, _NEG_LN2_HI_N_HALVES, x)
    r = _fused_by_constant(kd, _NEG_LN2_LO_N, _NEG_LN2_LO_N_HALVES, r)
    if tail is not None:
        r = tail + r
    index = (ki & _MASK_127).astype(np.intp)
    sbits = _EXP_SBITS[index] + ((ki + np.uint64(sign_bias)) << _U45)
    t1 = _fused_by_constant(r, _C3, _C3_HALVES, _C2)
    s = r + _EXP_TAIL[index]
    r2 = r * r
    t2 = _fused_by_constant(r, _C5, _C5_HALVES, _C4)
    u = _fused_multiply_add(t1, r2, s)
    tmp = _fused_multiply_add(r2 * r2, t2, u)
    return tmp, sbits, ki


def _special_case(tmp: np.ndarray, sbits: np.ndarray, ki: np.ndarray) -> np.ndarray:
    """``scale * (1 + tmp)`` where the scale's exponent overflowed or underflowed.

    The C routine's ``specialcase``: ``k > 0`` rescales by ``2^1009`` around a
    fused multiply-add, ``k < 0`` by ``2^-1022`` around a plain one, with the
    rounding fixed before the result is scaled into the subnormal range so it
    is rounded once.

    :param tmp: ``tmp`` from :func:`_exp_kernel`.
    :param sbits: The scale's bit pattern, exponent possibly out of range.
    :param ki: The rounded ``k``, as the C routine holds it.
    :return: The result.
    """
    out = np.empty(tmp.size, dtype=np.float64)
    positive = (ki & np.uint64(0x80000000)) == 0
    if positive.any():
        scale = (sbits[positive] - (np.uint64(1009) << _U52)).view(np.float64)
        with np.errstate(over="ignore"):
            fused = _fused_multiply_add(scale, tmp[positive], scale)
            out[positive] = fused * float.fromhex("0x1p1009")
    negative = ~positive
    if negative.any():
        out[negative] = _special_case_down(tmp[negative], sbits[negative])
    return out


def _special_case_down(tmp: np.ndarray, sbits: np.ndarray) -> np.ndarray:
    """The ``k < 0`` half of :func:`_special_case`, toward the subnormal range."""
    shifted = sbits + (np.uint64(1022) << _U52)
    scale = shifted.view(np.float64)
    product = scale * tmp
    y = scale + product
    one = np.where(y < 0.0, -1.0, 1.0)
    lo = (scale - y) + product
    hi = one + y
    lo = ((one - hi) + y) + lo
    narrowed = (hi + lo) - one
    signed_zero = (shifted & _SIGN).view(np.float64)
    # A result that vanished past the subnormals takes the scale's sign, read
    # off the bits: the magnitude bits are clear only on a signed zero.
    vanished = (narrowed.view(np.uint64) & _MAGNITUDE) == 0
    narrowed = np.where(vanished, signed_zero, narrowed)
    return np.where(np.abs(y) < 1.0, narrowed, y) * float.fromhex("0x1p-1022")


def _exp_from(x: np.ndarray, tail: np.ndarray | None) -> np.ndarray:
    """``exp(x + tail)`` for finite ``x`` with ``2^-54 <= |x| < 1024``."""
    tmp, sbits, ki = _exp_kernel(x, tail)
    large = _top(x) >= _TOP_LARGE
    if not large.any():
        scale = sbits.view(np.float64)
        return _fused_multiply_add(scale, tmp, scale)
    out = np.empty(x.size, dtype=np.float64)
    fast = ~large
    scale = sbits[fast].view(np.float64)
    out[fast] = _fused_multiply_add(scale, tmp[fast], scale)
    out[large] = _special_case(tmp[large], sbits[large], ki[large])
    return out


def _finish(
    flat: np.ndarray, tail: np.ndarray | None, *, finite_only: bool
) -> np.ndarray:
    """Route each argument to the fast path, the tiny path or the overflow edge."""
    top = _top(flat)
    tiny = top < _TOP_TINY
    huge = top >= _TOP_HUGE
    if not (tiny.any() or huge.any()):
        return _exp_from(flat, tail)
    out = np.empty(flat.size, dtype=np.float64)
    regular = ~(tiny | huge)
    if regular.any():
        out[regular] = _exp_from(flat[regular], None if tail is None else tail[regular])
    out[tiny] = 1.0 + flat[tiny]
    if huge.any():
        edge = flat[huge]
        beyond = np.where(edge > 0.0, np.inf, 0.0)
        if not finite_only:
            beyond = np.where(np.isnan(edge) | np.isposinf(edge), 1.0 + edge, beyond)
        out[huge] = beyond
    return out


def pinned_exp(values: np.ndarray | float) -> np.ndarray:
    """``exp`` elementwise, the bits glibc's routine returns, on every machine.

    Special values follow the C routine: ``exp(-inf)`` is ``0``, ``inf`` and
    ``nan`` propagate, arguments past the overflow or underflow threshold give
    ``inf`` or ``0``.

    :param values: Any real array-like.
    :return: The exponential, elementwise, in the same shape.
    :raises TypeError: if ``values`` holds a text or a value that is not a real number.
    """
    x = real_array(values, "values")
    flat = np.ascontiguousarray(x).reshape(-1)
    if not flat.size:
        return np.empty(x.shape, dtype=np.float64)
    return _finish(flat, None, finite_only=False).reshape(x.shape)


def _log_inline(ix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``pow``'s logarithm in double-double: ``hi + lo`` with about 15 extra bits.

    :param ix: Bit patterns of positive bases, subnormals already normalised.
    :return: ``(hi, lo)``.
    """
    tmp = ix - _POW_OFF
    index = ((tmp >> _U45) & _MASK_127).astype(np.intp)
    kd = (tmp.view(np.int64) >> np.int64(52)).astype(np.float64)
    z = (ix - (tmp & (np.uint64(0xFFF) << _U52))).view(np.float64)
    r = _fused_multiply_add(z, _POW_INVC[index], -1.0)
    t1 = _fused_by_constant(kd, _LN2_HI, _LN2_HI_HALVES, _POW_LOGC[index])
    lo1 = _fused_by_constant(kd, _LN2_LO, _LN2_LO_HALVES, _POW_LOGCTAIL[index])
    ar = _A[0] * r
    q1 = _fused_by_constant(r, _A[2], _A_HALVES[2], _A[1])
    q2 = _fused_by_constant(r, _A[4], _A_HALVES[4], _A[3])
    t2 = r + t1
    lo2 = (t1 - t2) + r
    ar2, lo3 = _two_product(ar, r)
    ar3 = r * ar2
    hi = t2 + ar2
    q3 = _fused_by_constant(r, _A[6], _A_HALVES[6], _A[5])
    lo4 = (t2 - hi) + ar2
    inner = _fused_multiply_add(q3, ar2, q2)
    poly = _fused_multiply_add(ar2, inner, q1)
    lo = _fused_multiply_add(ar3, poly, ((lo1 + lo2) + lo3) + lo4)
    y = hi + lo
    return y, (hi - y) + lo


_LN2_HI_HALVES = _split(_LN2_HI)
_LN2_LO_HALVES = _split(_LN2_LO)
_A_HALVES = tuple(_split(value) for value in _A)


def _normalised_bits(x: np.ndarray) -> np.ndarray:
    """Bit patterns of positive bases, subnormals rescaled as the C routine does."""
    ix = x.view(np.uint64).copy()
    subnormal = ix < np.uint64(0x0010000000000000)
    if subnormal.any():
        scaled = x[subnormal] * float.fromhex("0x1p52")
        ix[subnormal] = (scaled.view(np.uint64) & ~_SIGN) - (np.uint64(52) << _U52)
    return ix


def pinned_pow(base: np.ndarray | float, exponent: np.ndarray | float) -> np.ndarray:
    """``base ** exponent`` elementwise for a positive base, glibc's bits everywhere.

    The weighting design only ever raises a positive number to a finite
    power, so that is the domain spelled here; anything else is refused
    rather than answered by a branch nobody has checked.

    :param base: Positive finite values (subnormals included).
    :param exponent: Finite values, broadcast against *base*.
    :return: The power, elementwise, in the broadcast shape.
    :raises ValueError: If a base is not positive and finite, or an exponent
        is not finite.
    :raises TypeError: if ``base`` or ``exponent`` holds a text or a value that
        is not a real number.
    """
    x, y = np.broadcast_arrays(
        real_array(base, "base"), real_array(exponent, "exponent")
    )
    shape = x.shape
    x = np.ascontiguousarray(x).reshape(-1)
    y = np.ascontiguousarray(y).reshape(-1)
    if not (np.isfinite(x).all() and (x > 0.0).all() and np.isfinite(y).all()):
        message = "pinned_pow takes a positive finite base and a finite exponent."
        raise ValueError(message)
    if not x.size:
        return np.empty(shape, dtype=np.float64)
    top_y = _top(y)
    unit = x.view(np.uint64) == np.uint64(0x3FF0000000000000)
    small_y = top_y < _TOP_Y_TINY
    big_y = top_y >= _TOP_Y_HUGE
    trivial = unit | small_y | big_y
    if not trivial.any():
        return _pow_regular(x, y).reshape(shape)
    out = np.empty(x.size, dtype=np.float64)
    work = ~trivial
    if work.any():
        out[work] = _pow_regular(x[work], y[work])
    above_one = x.view(np.uint64) > np.uint64(0x3FF0000000000000)
    out[small_y] = np.where(above_one[small_y], 1.0 + y[small_y], 1.0 - y[small_y])
    grows = above_one[big_y] == (y[big_y] > 0.0)
    out[big_y] = np.where(grows, np.inf, 0.0)
    out[unit] = 1.0
    return out.reshape(shape)


def _pow_regular(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """The C routine's main path: ``exp(y log x)`` carried in double-double."""
    hi, lo = _log_inline(_normalised_bits(x))
    ehi, error = _two_product(y, hi)
    elo = _fused_multiply_add(y, lo, error)
    return _finish(ehi, elo, finite_only=True)
