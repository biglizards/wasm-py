//
// Created by dave on 19/11/2021.
//

#include "short.h"

Short* new_short(int a);

int short_eq(Short* a, Short* b) {
    return a->value == b->value;
}

int short_leq(Short* a, Short* b) {
    return a->value <= b->value;
}

Short* short_add(Short* a, Short* b) {
    Short* v = new_short(a->value + b->value);
    py_decref((PyObject*) a);
    py_decref((PyObject*) b);
    return v;
}

Short* short_sub(Short* a, Short* b) {
    Short* v = new_short(a->value - b->value);
    py_decref((PyObject*) a);
    py_decref((PyObject*) b);
    return v;
}

static PyNumberMethods numberMethods = {
        (binaryfunc) short_add,
        (binaryfunc) short_sub
};


Type SHORT = {
        TYPE_HEAD
        "short",                                      /* tp_name */
        sizeof(Short),           /* tp_basicsize */
        0,                              /* tp_itemsize */
        &numberMethods,
        NO_SEQUENCE_METHODS,
        NO_MAPPING_METHODS,
        (BinTest) short_eq,
        (BinTest) short_leq,
};


Short* new_short(int a) {
    Short* ptr;
    if (a < SHORT_SMALL_END && a >= SHORT_SMALL_START) {
        ptr = &small_shorts[a - SHORT_SMALL_START];
        ptr->Base.refCount++;
    } else {
        ptr = malloc(sizeof(Short));
        if (ptr == 0) {
            // out of memory! crash!
            printf("out of memory!\n");
            exit(1);
        }
        created_objects++;
        ptr->Base.type = &SHORT;
        ptr->Base.refCount = 1;
        ptr->value = a;
    }
    return ptr;
}

Short* short_fib(Short* a) {
    if (short_leq(a, &small_shorts[1])) {
        small_shorts[1].Base.refCount++;
        py_decref((PyObject*) a);
        return &small_shorts[1];
    }
    small_shorts[1].Base.refCount++;
    small_shorts[2].Base.refCount++;
    a->Base.refCount++;
    return short_add(
            short_fib(short_sub(a, &small_shorts[1])),
            short_fib(short_sub(a, &small_shorts[2]))
    );
}

#define NEW_SHORT(x) { 1, &SHORT, x }

Short small_shorts[SHORT_SMALL_END - SHORT_SMALL_START] = {
        NEW_SHORT(0),
        NEW_SHORT(1),
        NEW_SHORT(2),
        NEW_SHORT(3),
        NEW_SHORT(4),
        NEW_SHORT(5),
        NEW_SHORT(6),
        NEW_SHORT(7),
        NEW_SHORT(8),
        NEW_SHORT(9),
        NEW_SHORT(10),
        NEW_SHORT(11),
        NEW_SHORT(12),
        NEW_SHORT(13),
        NEW_SHORT(14),
        NEW_SHORT(15),
        NEW_SHORT(16),
        NEW_SHORT(17),
        NEW_SHORT(18),
        NEW_SHORT(19),
        NEW_SHORT(20),
        NEW_SHORT(21),
        NEW_SHORT(22),
        NEW_SHORT(23),
        NEW_SHORT(24),
        NEW_SHORT(25),
        NEW_SHORT(26),
        NEW_SHORT(27),
        NEW_SHORT(28),
        NEW_SHORT(29),
        NEW_SHORT(30),
        NEW_SHORT(31),
        NEW_SHORT(32),
        NEW_SHORT(33),
        NEW_SHORT(34),
        NEW_SHORT(35),
        NEW_SHORT(36),
        NEW_SHORT(37),
        NEW_SHORT(38),
        NEW_SHORT(39),
        NEW_SHORT(40),
        NEW_SHORT(41),
        NEW_SHORT(42),
        NEW_SHORT(43),
        NEW_SHORT(44),
        NEW_SHORT(45),
        NEW_SHORT(46),
        NEW_SHORT(47),
        NEW_SHORT(48),
        NEW_SHORT(49),
        NEW_SHORT(50),
        NEW_SHORT(51),
        NEW_SHORT(52),
        NEW_SHORT(53),
        NEW_SHORT(54),
        NEW_SHORT(55),
        NEW_SHORT(56),
        NEW_SHORT(57),
        NEW_SHORT(58),
        NEW_SHORT(59),
        NEW_SHORT(60),
        NEW_SHORT(61),
        NEW_SHORT(62),
        NEW_SHORT(63),
        NEW_SHORT(64),
        NEW_SHORT(65),
        NEW_SHORT(66),
        NEW_SHORT(67),
        NEW_SHORT(68),
        NEW_SHORT(69),
        NEW_SHORT(70),
        NEW_SHORT(71),
        NEW_SHORT(72),
        NEW_SHORT(73),
        NEW_SHORT(74),
        NEW_SHORT(75),
        NEW_SHORT(76),
        NEW_SHORT(77),
        NEW_SHORT(78),
        NEW_SHORT(79),
        NEW_SHORT(80),
        NEW_SHORT(81),
        NEW_SHORT(82),
        NEW_SHORT(83),
        NEW_SHORT(84),
        NEW_SHORT(85),
        NEW_SHORT(86),
        NEW_SHORT(87),
        NEW_SHORT(88),
        NEW_SHORT(89),
        NEW_SHORT(90),
        NEW_SHORT(91),
        NEW_SHORT(92),
        NEW_SHORT(93),
        NEW_SHORT(94),
        NEW_SHORT(95),
        NEW_SHORT(96),
        NEW_SHORT(97),
        NEW_SHORT(98),
        NEW_SHORT(99),
        NEW_SHORT(100),
        NEW_SHORT(101),
        NEW_SHORT(102),
        NEW_SHORT(103),
        NEW_SHORT(104),
        NEW_SHORT(105),
        NEW_SHORT(106),
        NEW_SHORT(107),
        NEW_SHORT(108),
        NEW_SHORT(109),
        NEW_SHORT(110),
        NEW_SHORT(111),
        NEW_SHORT(112),
        NEW_SHORT(113),
        NEW_SHORT(114),
        NEW_SHORT(115),
        NEW_SHORT(116),
        NEW_SHORT(117),
        NEW_SHORT(118),
        NEW_SHORT(119),
        NEW_SHORT(120),
        NEW_SHORT(121),
        NEW_SHORT(122),
        NEW_SHORT(123),
        NEW_SHORT(124),
        NEW_SHORT(125),
        NEW_SHORT(126),
        NEW_SHORT(127),
        NEW_SHORT(128),
        NEW_SHORT(129),
        NEW_SHORT(130),
        NEW_SHORT(131),
        NEW_SHORT(132),
        NEW_SHORT(133),
        NEW_SHORT(134),
        NEW_SHORT(135),
        NEW_SHORT(136),
        NEW_SHORT(137),
        NEW_SHORT(138),
        NEW_SHORT(139),
        NEW_SHORT(140),
        NEW_SHORT(141),
        NEW_SHORT(142),
        NEW_SHORT(143),
        NEW_SHORT(144),
        NEW_SHORT(145),
        NEW_SHORT(146),
        NEW_SHORT(147),
        NEW_SHORT(148),
        NEW_SHORT(149),
        NEW_SHORT(150),
        NEW_SHORT(151),
        NEW_SHORT(152),
        NEW_SHORT(153),
        NEW_SHORT(154),
        NEW_SHORT(155),
        NEW_SHORT(156),
        NEW_SHORT(157),
        NEW_SHORT(158),
        NEW_SHORT(159),
        NEW_SHORT(160),
        NEW_SHORT(161),
        NEW_SHORT(162),
        NEW_SHORT(163),
        NEW_SHORT(164),
        NEW_SHORT(165),
        NEW_SHORT(166),
        NEW_SHORT(167),
        NEW_SHORT(168),
        NEW_SHORT(169),
        NEW_SHORT(170),
        NEW_SHORT(171),
        NEW_SHORT(172),
        NEW_SHORT(173),
        NEW_SHORT(174),
        NEW_SHORT(175),
        NEW_SHORT(176),
        NEW_SHORT(177),
        NEW_SHORT(178),
        NEW_SHORT(179),
        NEW_SHORT(180),
        NEW_SHORT(181),
        NEW_SHORT(182),
        NEW_SHORT(183),
        NEW_SHORT(184),
        NEW_SHORT(185),
        NEW_SHORT(186),
        NEW_SHORT(187),
        NEW_SHORT(188),
        NEW_SHORT(189),
        NEW_SHORT(190),
        NEW_SHORT(191),
        NEW_SHORT(192),
        NEW_SHORT(193),
        NEW_SHORT(194),
        NEW_SHORT(195),
        NEW_SHORT(196),
        NEW_SHORT(197),
        NEW_SHORT(198),
        NEW_SHORT(199),
        NEW_SHORT(200),
        NEW_SHORT(201),
        NEW_SHORT(202),
        NEW_SHORT(203),
        NEW_SHORT(204),
        NEW_SHORT(205),
        NEW_SHORT(206),
        NEW_SHORT(207),
        NEW_SHORT(208),
        NEW_SHORT(209),
        NEW_SHORT(210),
        NEW_SHORT(211),
        NEW_SHORT(212),
        NEW_SHORT(213),
        NEW_SHORT(214),
        NEW_SHORT(215),
        NEW_SHORT(216),
        NEW_SHORT(217),
        NEW_SHORT(218),
        NEW_SHORT(219),
        NEW_SHORT(220),
        NEW_SHORT(221),
        NEW_SHORT(222),
        NEW_SHORT(223),
        NEW_SHORT(224),
        NEW_SHORT(225),
        NEW_SHORT(226),
        NEW_SHORT(227),
        NEW_SHORT(228),
        NEW_SHORT(229),
        NEW_SHORT(230),
        NEW_SHORT(231),
        NEW_SHORT(232),
        NEW_SHORT(233),
        NEW_SHORT(234),
        NEW_SHORT(235),
        NEW_SHORT(236),
        NEW_SHORT(237),
        NEW_SHORT(238),
        NEW_SHORT(239),
        NEW_SHORT(240),
        NEW_SHORT(241),
        NEW_SHORT(242),
        NEW_SHORT(243),
        NEW_SHORT(244),
        NEW_SHORT(245),
        NEW_SHORT(246),
        NEW_SHORT(247),
        NEW_SHORT(248),
        NEW_SHORT(249),
        NEW_SHORT(250),
        NEW_SHORT(251),
        NEW_SHORT(252),
        NEW_SHORT(253),
        NEW_SHORT(254),
        NEW_SHORT(255),
};