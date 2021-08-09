# # with bound fix 
# ## WITHOUT ERROR FILTRATION ## 
# total number of models 910
# copasi runs 593 avoid 317
# supported 593
# translates 585, 98.651%, fails 8
# runnable 543, 92.821%, fails 42
# success 543, 100.000%, fails 0
# exact count: 369 (68.0%), high vr count: 416 (76.6%)
# # without bound fix 
#  ## WITHOUT ERROR FILTRATION ## 
# total number of models 910
# copasi runs 593 avoid 317
# supported 593
# translates 585, 98.651%, fails 8
# runnable 545, 93.162%, fails 40
# success 545, 100.000%, fails 0
# exact count: 372 (68.3%), high vr count: 416 (76.3%)


# with bound fix 
wfix = set([2, 17, 19, 23, 32, 41, 42, 46, 49, 68, 72, 91, 93, 94, 123, 143, 147, 151, 163, 175, 182, 190, 192, 197, 198, 199, 200, 202, 210, 211, 216, 220, 223, 225, 226, 231, 239, 240, 246, 252, 253, 271, 272, 289, 290, 292, 299, 304, 315, 320, 321, 328, 330, 331, 343, 345, 346, 347, 353, 367, 371, 373, 374, 377, 380, 383, 384, 386, 387, 388, 389, 390, 394, 395, 397, 399, 406, 407, 409, 410, 415, 428, 434, 435, 446, 452, 453, 454, 455, 456, 464, 475, 478, 482, 489, 504, 510, 511, 513, 514, 515, 516, 523, 524, 525, 526, 533, 543, 544, 545, 546, 548, 560, 565, 569, 572, 576, 579, 581, 583, 584, 585, 586, 587, 588, 594, 600, 602, 611, 618, 619, 630, 633, 639, 641, 642, 670, 671, 679, 680, 689, 690, 691, 692, 700, 737, 738, 740, 836, 843, 844, 861, 869, 870, 871])
# without bound fix 
wofix = set([2, 13, 15, 17, 18, 19, 23, 32, 38, 41, 42, 46, 49, 61, 68, 72, 76, 91, 93, 94, 123, 143, 147, 151, 163, 175, 182, 190, 192, 197, 198, 199, 200, 202, 210, 211, 216, 218, 219, 220, 221, 222, 223, 225, 226, 231, 239, 240, 246, 253, 257, 266, 271, 272, 289, 290, 299, 304, 315, 320, 321, 328, 330, 331, 346, 347, 353, 371, 373, 374, 377, 380, 383, 384, 386, 387, 388, 389, 390, 392, 393, 394, 395, 397, 399, 406, 407, 409, 410, 415, 428, 434, 435, 446, 452, 453, 454, 455, 456, 464, 475, 478, 482, 489, 495, 504, 510, 511, 513, 514, 515, 516, 523, 524, 525, 526, 543, 544, 545, 546, 560, 565, 569, 572, 576, 579, 581, 583, 584, 586, 587, 588, 594, 600, 602, 611, 619, 630, 633, 639, 679, 689, 690, 691, 692, 700, 737, 738, 843, 844, 861, 869, 870, 871])
# with fix
wfix_run = [203, 204, 209, 250, 279, 300, 306, 307, 308, 309, 310, 311, 376, 378, 392, 393, 396, 398, 401, 402, 417, 418, 419, 420, 421, 499, 507, 522, 617, 643, 644, 645, 687, 688, 705, 730, 748, 757, 802, 815, 837, 880]
# w/o fix
wofix_run = [203, 204, 209, 250, 279, 300, 306, 307, 308, 309, 310, 311, 376, 378, 396, 398, 401, 402, 417, 418, 419, 420, 421, 499, 507, 522, 617, 643, 644, 645, 687, 688, 705, 730, 748, 757, 802, 815, 837, 880]
import IPython;IPython.embed()