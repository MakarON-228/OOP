class TLogElement:
    def __init__(self):
        self.__in1 = False
        self.__in2 = False
        self._res = False
        self.__nextEl = None
        self.__nextIn = 0
        if not hasattr(self, "calc"):
            raise NotImplementedError("Нельзя создать такой объект!")

    def __setIn1(self, newIn1):
        self.__in1 = newIn1
        self.calc()
        if self.__nextEl:
            if self.__nextIn == 1:
                self.__nextEl.In1 = self._res
            elif self.__nextIn == 2:
                self.__nextEl.In2 = self._res

    def __setIn2(self, newIn2):
        self.__in2 = newIn2
        self.calc()
        if self.__nextEl:
            if self.__nextIn == 1:
                self.__nextEl.In1 = self._res
            elif self.__nextIn == 2:
                self.__nextEl.In2 = self._res

    In1 = property(lambda x: x.__in1, __setIn1)
    In2 = property(lambda x: x.__in2, __setIn2)
    Res = property(lambda x: x._res)

    def link(self, nextEl, nextIn):
        self.__nextEl = nextEl
        self.__nextIn = nextIn


class TNot(TLogElement):
    def __init__(self):
        TLogElement.__init__(self)

    def calc(self):
        self._res = not self.In1


class TLog2In(TLogElement):
    pass


class TAnd(TLog2In):
    def __init__(self):
        TLog2In.__init__(self)

    def calc(self):
        self._res = self.In1 and self.In2


class TOr(TLog2In):
    def __init__(self):
        TLog2In.__init__(self)

    def calc(self):
        self._res = self.In1 or self.In2


elNot1 = TNot()
elNot2 = TNot()
elAnd1 = TAnd()
elAnd2 = TAnd()
elXOr = TOr()

elNot1.link(elAnd1, 2)
elNot2.link(elAnd2, 1)

elAnd1.link(elXOr, 1)
elAnd2.link(elXOr, 2)

print(" A | B | ab' + a'b ");
print("-------------------");
for i in range(2):
    for j in range(2):
        a, b = bool(i), bool(j)
        elNot1.In1 = b
        elNot2.In1 = a
        elAnd1.In1 = a
        elAnd2.In2 = b
        print(i, j, int(elXOr.Res))