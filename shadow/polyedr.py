from math import *
from functools import reduce
from operator import add
from common.r3 import R3
from common.tk_drawer import TkDrawer


class Segment:
    """ Одномерный отрезок """
    # Параметры конструктора: начало и конец отрезка (числа)

    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin

    # Отрезок вырожден?
    def is_degenerate(self):
        return self.beg >= self.fin

    # Пересечение с отрезком
    def intersect(self, other):
        if other.beg > self.beg:
            self.beg = other.beg
        if other.fin < self.fin:
            self.fin = other.fin
        return self

    # Разность отрезков
    # Разность двух отрезков всегда является списком из двух отрезков!
    def subtraction(self, other):
        return [Segment(
            self.beg, self.fin if self.fin < other.beg else other.beg),
            Segment(self.beg if self.beg > other.fin else other.fin, self.fin)]


class Edge:
    """ Ребро полиэдра """
    # Начало и конец стандартного одномерного отрезка
    SBEG, SFIN = 0.0, 1.0

    # Параметры конструктора: начало и конец ребра (точки в R3)
    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin
        # Список «просветов»
        self.gaps = [Segment(Edge.SBEG, Edge.SFIN)]

    # Учёт тени от одной грани
    def shadow(self, facet):
        # «Вертикальная» грань не затеняет ничего
        if facet.is_vertical():
            return
        # Нахождение одномерной тени на ребре
        shade = Segment(Edge.SBEG, Edge.SFIN)
        for u, v in zip(facet.vertexes, facet.v_normals()):
            shade.intersect(self.intersect_edge_with_normal(u, v))
            if shade.is_degenerate():
                return

        shade.intersect(
            self.intersect_edge_with_normal(
                facet.vertexes[0], facet.h_normal()))
        if shade.is_degenerate():
            return
        # Преобразование списка «просветов», если тень невырождена
        gaps = [s.subtraction(shade) for s in self.gaps]
        self.gaps = [
            s for s in reduce(add, gaps, []) if not s.is_degenerate()]

    # Преобразование одномерных координат в трёхмерные
    def r3(self, t):
        return self.beg * (Edge.SFIN - t) + self.fin * t

    # Пересечение ребра с полупространством, задаваемым точкой (a)
    # на плоскости и вектором внешней нормали (n) к ней
    def intersect_edge_with_normal(self, a, n):
        f0, f1 = n.dot(self.beg - a), n.dot(self.fin - a)
        if f0 >= 0.0 and f1 >= 0.0:
            return Segment(Edge.SFIN, Edge.SBEG)
        if f0 < 0.0 and f1 < 0.0:
            return Segment(Edge.SBEG, Edge.SFIN)
        x = - f0 / (f1 - f0)
        return Segment(Edge.SBEG, x) if f0 < 0.0 else Segment(x, Edge.SFIN)


class Facet:
    """ Грань полиэдра """
    # Параметры конструктора: список вершин

    def __init__(self, vertexes, origin_vertexes):
        self.vertexes = vertexes
        self.origin_vertexes = origin_vertexes

        self.edges = []
        self.origin_edges = []
        for i in range(len(self.vertexes)):
            self.edges.append(Edge(self.vertexes[i-1], self.vertexes[i]))

        for i in range(len(self.origin_vertexes)):
            self.origin_edges.append(
                Edge(self.origin_vertexes[i-1], self.origin_vertexes[i]))
    # «Вертикальна» ли грань?

    def is_vertical(self):
        return self.h_normal().dot(Polyedr.V) == 0.0

    # Нормаль к «горизонтальному» полупространству
    def h_normal(self):
        n = (
            self.vertexes[1] - self.vertexes[0]).cross(
            self.vertexes[2] - self.vertexes[0])
        return n * (-1.0) if n.dot(Polyedr.V) < 0.0 else n

    # Нормали к «вертикальным» полупространствам, причём k-я из них
    # является нормалью к грани, которая содержит ребро, соединяющее
    # вершины с индексами k-1 и k
    def v_normals(self):
        return [self._vert(x) for x in range(len(self.vertexes))]

    # Вспомогательный метод
    def _vert(self, k):
        n = (self.vertexes[k] - self.vertexes[k - 1]).cross(Polyedr.V)
        return n * \
            (-1.0) if n.dot(self.vertexes[k - 1] - self.center()) < 0.0 else n

    # Центр грани
    def center(self):
        return sum(self.vertexes, R3(0.0, 0.0, 0.0)) * \
            (1.0 / len(self.vertexes))

    def origin_center(self):
        return sum(self.origin_vertexes, R3(0.0, 0.0, 0.0)) * \
            (1.0 / len(self.origin_vertexes))

        # Центр грани внутри единичного куба?
    def center_in_unit_cube(self):
        return (abs(self.origin_center().x) <= 0.5 and
                abs(self.origin_center().y) <= 0.5 and
                abs(self.origin_center().z) <= 0.5)

    def angle(self):
        n1 = Polyedr.V
        n2 = self.h_normal()
        n3 = n1.dot(n2)
        angle = acos(n3 / sqrt(n2.x ** 2 + n2.y ** 2 + n2.z ** 2))
        return angle

    def triandle_area(self, a, b, c):
        pre_area = (b - a).cross(c-a)
        # вычисление модуля векторного произвеения
        area = 0.5 * sqrt(pre_area.x ** 2 +
                          pre_area.y ** 2 + pre_area.z ** 2)
        return area

    def facet_area(self):
        area = 0.0
        for e in self.origin_edges:
            area += self.triandle_area(self.origin_center(), e.beg, e.fin)
        return area


class Polyedr:
    """ Полиэдр """
    # вектор проектирования
    V = R3(0.0, 0.0, 1.0)
    # Параметры конструктора: файл, задающий полиэдр

    def __init__(self, file):

        # списки вершин, рёбер и граней полиэдра
        self.vertexes, self.edges, self.origin_edges, = [], [], []
        self.facets, self.origin_vertexes, = [], []

        # список строк файла
        with open(file) as f:
            for i, line in enumerate(f):
                if i == 0:
                    # обрабатываем первую строку; buf - вспомогательный массив
                    buf = line.split()
                    # коэффициент гомотетии
                    c = float(buf.pop(0))
                    global h
                    h = c
                    # углы Эйлера, определяющие вращение
                    alpha, beta, gamma = (float(x) * pi / 180.0 for x in buf)
                elif i == 1:
                    # во второй строке число вершин, граней и рёбер полиэдра
                    nv, nf, ne = (int(x) for x in line.split())
                elif i < nv + 2:
                    # задание всех вершин полиэдра
                    x, y, z = (float(x) for x in line.split())
                    self.vertexes.append(R3(x, y, z).rz(
                        alpha).ry(beta).rz(gamma) * c)
                    self.origin_vertexes.append(R3(x, y, z))
                else:
                    # вспомогательный массив
                    buf = line.split()
                    # количество вершин очередной грани
                    size = int(buf.pop(0))
                    # массив вершин этой грани
                    vertexes = list(self.vertexes[int(n) - 1] for n in buf)
                    origin_vertexes = list(
                        self.origin_vertexes[int(n) - 1] for n in buf)
                    # задание рёбер грани
                    for n in range(size):
                        self.edges.append(Edge(vertexes[n - 1], vertexes[n]))
                        self.origin_edges.append(
                            Edge(origin_vertexes[n - 1], origin_vertexes[n]))
                    # задание самой грани
                    self.facets.append(Facet(vertexes, origin_vertexes))

        # Удаление дубликатов рёбер
    def edges_uniq(self):
        edges = {}
        for e in self.edges:
            if (e.beg, e.fin) not in edges and (e.fin, e.beg) not in edges:
                edges[(e.beg, e.fin)] = e
        self.edges = list(edges.values())

    def draw(self, tk):  # pragma: no cover
        tk.clean()
        for e in self.edges:
            for f in self.facets:
                e.shadow(f)
            for s in e.gaps:
                tk.draw_line(e.r3(s.beg), e.r3(s.fin))

    def modification(self):
        area = 0.0
        self.edges_uniq()
        for f in self.facets:
            flag = False
            for e in f.edges:
                for g in self.facets:
                    e.shadow(g)
            # если просветов нет то ребро полностью невидимо
                if len(e.gaps) != 0:
                    flag = True
            if not (f.center_in_unit_cube())\
                and f.angle() <= pi/7\
                    and not (flag):
                area += f.facet_area()
        return area
