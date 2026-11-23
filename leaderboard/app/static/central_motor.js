/*
 * Motor de «Central de Emergencias» para el navegador: traduccion 1:1 de game/clases/CentralEmergencias.py
 * (simulacion, Dijkstra, BFS, ordenes y puntuacion). Solo enteros y paso fijo de 30 ticks/s. El mapa, las
 * constantes y el escenario llegan del servidor (config_cliente), asi que no hay numeros duplicados.
 * tests/test_central_web.py ejecuta este archivo en Node con las mismas ordenes que el motor de Python y exige
 * el mismo estado tick a tick. El servidor rejuega la lista de ordenes que produce (CentralEmergencias.rejugar).
 */
(function (raiz) {
  "use strict";
  function piso(a, b) { return Math.floor(a / b); }
  var INF = Math.pow(2, 40);

  // ---------- cola de prioridad por (distancia, vertice): el mismo orden que heapq con tuplas ----------
  function menor(x, y) { return x[0] < y[0] || (x[0] === y[0] && x[1] < y[1]); }
  function Cola() { this.h = []; }
  Cola.prototype.push = function (e) {
    var h = this.h; h.push(e); var i = h.length - 1;
    while (i > 0) { var p = (i - 1) >> 1; if (!menor(h[i], h[p])) break; var t = h[i]; h[i] = h[p]; h[p] = t; i = p; }
  };
  Cola.prototype.pop = function () {
    var h = this.h, top = h[0], ult = h.pop();
    if (h.length) {
      h[0] = ult; var i = 0;
      for (;;) {
        var l = 2 * i + 1, r = l + 1, m = i;
        if (l < h.length && menor(h[l], h[m])) m = l;
        if (r < h.length && menor(h[r], h[m])) m = r;
        if (m === i) break;
        var t = h[i]; h[i] = h[m]; h[m] = t; i = m;
      }
    }
    return top;
  };

  function igual(a, b) {
    if (a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }

  // ---------- mapa y grafo dinamico ----------
  function Mapa(cfg) {
    this.nodos = cfg.nodos; this.calles = cfg.calles; this.base = cfg.base;
    this.hospitales = cfg.hospitales; this.amb = cfg.ambulancias; this.gravedad = cfg.gravedad;
    this.k = cfg.constantes;
    var ady = [];
    for (var n = 0; n < this.nodos.length; n++) ady.push([]);
    for (var i = 0; i < this.calles.length; i++) {
      var a = this.calles[i][0], b = this.calles[i][1];
      ady[a].push([b, i]); ady[b].push([a, i]);
    }
    for (n = 0; n < ady.length; n++) ady[n].sort(function (x, y) { return x[0] - y[0] || x[1] - y[1]; });
    this.ady = ady;
  }
  Mapa.prototype.arista_entre = function (a, b) {
    var l = this.ady[a];
    for (var k = 0; k < l.length; k++) if (l[k][0] === b) return l[k][1];
    return -1;
  };

  function Grafo(mapa) {
    this.m = mapa;
    var n = mapa.calles.length;
    this.bloqueada = []; this.trafico = []; this.aviso = [];
    for (var i = 0; i < n; i++) { this.bloqueada.push(false); this.trafico.push(0); this.aviso.push(false); }
  }
  Grafo.prototype.coste = function (i, prioridad) {
    if (prioridad) return this.m.base[i];
    return piso(this.m.base[i] * this.m.k.NIVELES_TRAFICO[this.trafico[i]], 100);
  };
  Grafo.prototype.dijkstra = function (origen, destino, prioridad, penalizadas) {
    var n = this.m.nodos.length, dist = [], previo = [], via = [];
    for (var k = 0; k < n; k++) { dist.push(INF); previo.push(-1); via.push(-1); }
    dist[origen] = 0;
    var cola = new Cola(); cola.push([0, origen]);
    while (cola.h.length) {
      var top = cola.pop(), d = top[0], u = top[1];
      if (d > dist[u]) continue;
      if (u === destino) break;
      var l = this.m.ady[u];
      for (var j = 0; j < l.length; j++) {
        var v = l[j][0], i = l[j][1];
        if (this.bloqueada[i]) continue;
        var c = this.coste(i, prioridad);
        if (penalizadas && penalizadas[i]) c *= 4;
        var nd = d + c;
        if (nd < dist[v]) { dist[v] = nd; previo[v] = u; via[v] = i; cola.push([nd, v]); }
      }
    }
    if (dist[destino] >= INF) return null;
    var nodos = [destino], aristas = [];
    while (nodos[nodos.length - 1] !== origen) {
      aristas.push(via[nodos[nodos.length - 1]]);
      nodos.push(previo[nodos[nodos.length - 1]]);
    }
    nodos.reverse(); aristas.reverse();
    var total = 0;
    for (k = 0; k < aristas.length; k++) total += this.coste(aristas[k], prioridad);
    return [total, nodos, aristas];
  };
  Grafo.prototype.bfs = function (origenes) {
    var visto = [], cola = [], cab = 0;
    for (var k = 0; k < this.m.nodos.length; k++) visto.push(false);
    for (k = 0; k < origenes.length; k++) if (!visto[origenes[k]]) { visto[origenes[k]] = true; cola.push(origenes[k]); }
    while (cab < cola.length) {
      var u = cola[cab++], l = this.m.ady[u];
      for (var j = 0; j < l.length; j++) {
        var v = l[j][0], i = l[j][1];
        if (!this.bloqueada[i] && !visto[v]) { visto[v] = true; cola.push(v); }
      }
    }
    return visto;
  };
  Grafo.prototype.aislados = function () {
    var o = [];
    for (var h = 0; h < this.m.hospitales.length; h++) o.push(this.m.hospitales[h][1]);
    var visto = this.bfs(o), res = [];
    for (var k = 0; k < visto.length; k++) if (!visto[k]) res.push(k);
    return res;
  };

  // ---------- partida ----------
  function Central(cfg) {
    this.m = new Mapa(cfg);
    var esc = cfg.escenario, K = this.m.k;
    this.esc = esc; this.K = K;
    this.g = new Grafo(this.m);
    this.tick = 0;
    this.fin_tick = esc.duracion;
    this.ambulancias = [];
    for (var k = 0; k < this.m.amb.length; k++) {
      this.ambulancias.push({k: k, numero: this.m.amb[k][0], nodo: this.m.amb[k][1], activa: false, estado: "inactiva", ruta: [],
        arista: -1, hacia: -1, prog: 0, dur: 0, objetivo: null, paciente: -1, espera: 0, prioridad_hasta: -1,
        bloqueo_avisado: false, recorrido: 0});
    }
    this.ambulancias[0].activa = true; this.ambulancias[0].estado = "libre";
    this.emergencias = [];
    this.camas = this.m.hospitales.map(function (h) { return h[2]; });
    this.recursos = {despejar: esc.recursos.despejar, prioridad: esc.recursos.prioridad};
    this.despejes = [];
    this.pendientes = esc.eventos.slice();
    this.total = esc.eventos.filter(function (e) { return e.tipo === "emergencia"; }).length;
    this.fase = 1; this.estado = "jugando";
    this.ordenes = []; this.desvios = 0; this.usados = {despejar: 0, prioridad: 0};
    this.eventos = []; this.cola = [];
  }
  var C = Central.prototype;
  C.jugando = function () { return this.estado === "jugando"; };
  C.emergencia = function (id) {
    for (var k = 0; k < this.emergencias.length; k++) if (this.emergencias[k].id === id) return this.emergencias[k];
    return null;
  };
  C.origen_de = function (a) { return a.arista >= 0 ? a.hacia : a.nodo; };
  C.prio = function (a) { return this.tick < a.prioridad_hasta; };
  C.opciones = function (origen, destino, prioridad) {
    if (origen === destino) return [[0, [origen], []]];
    var a = this.g.dijkstra(origen, destino, prioridad, null);
    if (!a) return [];
    var n = this.m.calles.length, pen = [], usa = false, k;
    for (k = 0; k < a[2].length; k++) if (this.g.aviso[a[2][k]]) usa = true;
    if (usa) pen = this.g.aviso.slice();
    else { for (k = 0; k < n; k++) pen.push(false); for (k = 0; k < a[2].length; k++) pen[a[2][k]] = true; }
    var b = this.g.dijkstra(origen, destino, prioridad, pen);
    if (!b || igual(b[1], a[1])) return [a];
    return [a, b];
  };
  C.eta_hospitales = function (a) {
    var res = [];
    for (var h = 0; h < this.m.hospitales.length; h++) {
      var op = this.opciones(this.origen_de(a), this.m.hospitales[h][1], this.prio(a));
      res.push([h, op.length ? op[0][0] : -1, this.camas[h]]);
    }
    return res;
  };
  C.ordenar = function (tipo, a, b, c) { this.cola.push([this.tick, tipo, a || 0, b || 0, c || 0]); };
  C._aplicar = function (o) {
    var ok = false, t = o[1];
    if (t === "despachar") ok = this._despachar(o[2], o[3], o[4]);
    else if (t === "hospital") ok = this._hospital(o[2], o[3], o[4]);
    else if (t === "desviar") ok = this._desviar(o[2], o[3]);
    else if (t === "despejar") ok = this._despejar(o[2]);
    else if (t === "prioridad") ok = this._prioridad(o[2]);
    if (ok) this.ordenes.push(o.slice());
    return ok;
  };
  C._fijar_ruta = function (a, nodos) {
    a.ruta = nodos.slice(1);
    a.bloqueo_avisado = false;
    if (a.arista < 0) a.estado = a.ruta.length ? "ruta" : a.estado;
  };
  C._despachar = function (k, id, opcion) {
    if (!(k >= 0 && k < this.ambulancias.length)) return false;
    var a = this.ambulancias[k], e = this.emergencia(id);
    if (!a.activa || a.estado !== "libre" || !e || e.estado !== "espera") return false;
    var op = this.opciones(this.origen_de(a), e.nodo, this.prio(a));
    if (!(opcion >= 0 && opcion < op.length)) return false;
    e.estado = "asignada"; e.ambulancia = k; e.despachada = this.tick;
    a.objetivo = ["paciente", id]; a.estado = "ruta";
    this._fijar_ruta(a, op[opcion][1]);
    this.eventos.push([this.tick, "despacho", k]);
    if (!a.ruta.length) this._llegar(a);
    return true;
  };
  C._hospital = function (k, h, opcion) {
    if (!(k >= 0 && k < this.ambulancias.length) || !(h >= 0 && h < this.m.hospitales.length)) return false;
    var a = this.ambulancias[k];
    if (a.estado !== "esperando_hospital" || this.camas[h] <= 0) return false;
    var op = this.opciones(this.origen_de(a), this.m.hospitales[h][1], this.prio(a));
    if (!(opcion >= 0 && opcion < op.length)) return false;
    this.camas[h] -= 1;
    this.emergencia(a.paciente).hospital = h;
    a.objetivo = ["hospital", h]; a.estado = "ruta";
    this._fijar_ruta(a, op[opcion][1]);
    this.eventos.push([this.tick, "hacia_hospital", k]);
    if (!a.ruta.length) this._llegar(a);
    return true;
  };
  C._destino = function (a) {
    return a.objetivo[0] === "paciente" ? this.emergencia(a.objetivo[1]).nodo : this.m.hospitales[a.objetivo[1]][1];
  };
  C._desviar = function (k, opcion) {
    if (!(k >= 0 && k < this.ambulancias.length)) return false;
    var a = this.ambulancias[k];
    if ((a.estado !== "ruta" && a.estado !== "detenida") || a.objetivo === null) return false;
    var op = this.opciones(this.origen_de(a), this._destino(a), this.prio(a));
    if (!(opcion >= 0 && opcion < op.length)) return false;
    if (igual(op[opcion][1].slice(1), a.ruta)) return false;
    this._fijar_ruta(a, op[opcion][1]);
    if (a.arista < 0) a.estado = "ruta";
    this.desvios += 1;
    this.eventos.push([this.tick, "desvio", k]);
    return true;
  };
  C._despejar = function (i) {
    if (!(i >= 0 && i < this.m.calles.length) || !this.g.bloqueada[i] || this.recursos.despejar <= 0) return false;
    for (var k = 0; k < this.despejes.length; k++) if (this.despejes[k][1] === i) return false;
    this.recursos.despejar -= 1; this.usados.despejar += 1;
    this.despejes.push([this.tick + this.K.DESPEJE, i]);
    this.eventos.push([this.tick, "mediacion", i]);
    return true;
  };
  C._prioridad = function (k) {
    if (!(k >= 0 && k < this.ambulancias.length) || this.recursos.prioridad <= 0) return false;
    var a = this.ambulancias[k];
    if (!a.activa || a.estado === "inactiva" || this.tick < a.prioridad_hasta) return false;
    this.recursos.prioridad -= 1; this.usados.prioridad += 1;
    a.prioridad_hasta = this.tick + this.K.PRIORIDAD;
    this.eventos.push([this.tick, "prioridad", k]);
    return true;
  };
  C._aristas_ruta = function (a) {
    var res = [], previo = this.origen_de(a);
    for (var k = 0; k < a.ruta.length; k++) { res.push(this.m.arista_entre(previo, a.ruta[k])); previo = a.ruta[k]; }
    if (a.arista >= 0 && a.ruta.length && a.ruta[0] === a.hacia) res = res.slice(1);
    return res;
  };
  C._evento = function (e) {
    var t = e.tipo, k;
    if (t === "emergencia") {
      var em = {id: e.id, nodo: e.nodo, gravedad: e.gravedad, aparece: this.tick, limite: this.tick + e.limite,
        estado: "espera", ambulancia: -1, despachada: -1, entregada: -1, hospital: -1};
      this.emergencias.push(em);
      this.eventos.push([this.tick, "emergencia", em.id]);
    } else if (t === "aviso") {
      this.g.aviso[e.arista] = true;
      this.eventos.push([this.tick, "aviso", e.arista]);
    } else if (t === "bloqueo") {
      var i = e.arista;
      this.g.bloqueada[i] = true; this.g.aviso[i] = false;
      this.eventos.push([this.tick, "bloqueo", i]);
      for (k = 0; k < this.ambulancias.length; k++) {
        var a = this.ambulancias[k];
        if (this._aristas_ruta(a).indexOf(i) >= 0) { a.bloqueo_avisado = true; this.eventos.push([this.tick, "ruta_bloqueada", a.k]); }
      }
    } else if (t === "apertura") {
      if (this.g.bloqueada[e.arista]) { this.g.bloqueada[e.arista] = false; this.eventos.push([this.tick, "apertura", e.arista]); }
    } else if (t === "trafico") {
      this.g.trafico[e.arista] = e.nivel;
    } else if (t === "refuerzo") {
      var r = this.ambulancias[e.ambulancia];
      r.activa = true; r.estado = "libre";
      this.eventos.push([this.tick, "refuerzo", r.k]);
    } else if (t === "fase") {
      this.fase = e.fase;
      this.eventos.push([this.tick, "fase", e.fase]);
    }
  };
  C._mover = function (a) {
    if (a.estado === "recogiendo" || a.estado === "entregando") {
      a.espera -= 1; if (a.espera <= 0) this._fin_espera(a); return;
    }
    if (a.estado === "esperando_hospital") {
      a.espera -= 1; if (a.espera <= 0) this._auto_hospital(a); return;
    }
    if (a.arista >= 0) {
      a.prog += 1; a.recorrido += 1;
      if (a.prog >= a.dur) {
        a.nodo = a.hacia; a.arista = -1; a.prog = 0;
        if (a.ruta.length && a.ruta[0] === a.nodo) a.ruta.shift();
        if (!a.ruta.length) this._llegar(a);
      }
      return;
    }
    if ((a.estado === "ruta" || a.estado === "detenida") && a.ruta.length) {
      var sig = a.ruta[0], i = this.m.arista_entre(a.nodo, sig);
      if (i < 0 || this.g.bloqueada[i]) {
        if (a.estado !== "detenida") { a.estado = "detenida"; this.eventos.push([this.tick, "detenida", a.k]); }
        return;
      }
      a.estado = "ruta"; a.arista = i; a.hacia = sig; a.prog = 0;
      a.dur = Math.max(1, this.g.coste(i, this.prio(a)));
    }
  };
  C._llegar = function (a) {
    if (a.objetivo === null) { a.estado = "libre"; return; }
    if (a.objetivo[0] === "paciente") {
      var e = this.emergencia(a.objetivo[1]);
      if (e.estado !== "asignada") { a.objetivo = null; a.estado = "libre"; return; }
      e.estado = "atendiendo";
      a.estado = "recogiendo"; a.espera = this.K.RECOGER;
      this.eventos.push([this.tick, "en_escena", a.k]);
    } else {
      a.estado = "entregando"; a.espera = this.K.ENTREGA;
      this.eventos.push([this.tick, "en_hospital", a.k]);
    }
  };
  C._fin_espera = function (a) {
    var e;
    if (a.estado === "recogiendo") {
      e = this.emergencia(a.objetivo[1]);
      e.estado = "traslado"; a.paciente = e.id; a.objetivo = null;
      a.estado = "esperando_hospital"; a.espera = this.K.AUTO_HOSPITAL;
      this.eventos.push([this.tick, "paciente_a_bordo", a.k]);
    } else {
      e = this.emergencia(a.paciente);
      e.entregada = this.tick;
      e.estado = this.tick <= e.limite ? "a_tiempo" : "tarde";
      a.paciente = -1; a.objetivo = null; a.estado = "libre";
      this.eventos.push([this.tick, "entregado", e.id]);
    }
  };
  C._auto_hospital = function (a) {
    var mejor = null, l = this.eta_hospitales(a);
    for (var k = 0; k < l.length; k++) {
      if (l[k][2] > 0 && l[k][1] >= 0 && (mejor === null || l[k][1] < mejor[1])) mejor = [l[k][0], l[k][1]];
    }
    if (mejor !== null) { this._hospital(a.k, mejor[0], 0); this.eventos.push([this.tick, "auto_hospital", a.k]); }
    else a.espera = this.K.TICKS_S;
  };
  C.avanzar = function () {
    if (!this.jugando()) return;
    var k, cola = this.cola; this.cola = [];
    for (k = 0; k < cola.length; k++) this._aplicar(cola[k]);
    while (this.pendientes.length && this.pendientes[0].t <= this.tick) this._evento(this.pendientes.shift());
    var copia = this.despejes.slice();
    for (k = 0; k < copia.length; k++) {
      if (copia[k][0] <= this.tick) {
        for (var j = 0; j < this.despejes.length; j++) {
          if (this.despejes[j][0] === copia[k][0] && this.despejes[j][1] === copia[k][1]) { this.despejes.splice(j, 1); break; }
        }
        var i = copia[k][1];
        if (this.g.bloqueada[i]) { this.g.bloqueada[i] = false; this.eventos.push([this.tick, "apertura", i]); }
      }
    }
    if (this.tick > 0 && this.tick % this.K.CAMA_CADA === 0) {
      for (k = 0; k < this.m.hospitales.length; k++) if (this.camas[k] < this.m.hospitales[k][2]) this.camas[k] += 1;
    }
    for (k = 0; k < this.ambulancias.length; k++) if (this.ambulancias[k].activa) this._mover(this.ambulancias[k]);
    for (k = 0; k < this.emergencias.length; k++) {
      var e = this.emergencias[k];
      if ((e.estado === "espera" || e.estado === "asignada") && this.tick > e.limite) {
        e.estado = "sin_atender";
        this.eventos.push([this.tick, "sin_atender", e.id]);
        for (var m = 0; m < this.ambulancias.length; m++) {
          var a = this.ambulancias[m];
          if (a.objetivo !== null && a.objetivo[0] === "paciente" && a.objetivo[1] === e.id) {
            a.objetivo = null; a.ruta = [];
            if (a.arista < 0) a.estado = "libre";
          }
        }
      }
    }
    this.tick += 1;
    var resueltas = 0, quedan = false;
    for (k = 0; k < this.emergencias.length; k++) {
      var s = this.emergencias[k].estado;
      if (s === "a_tiempo" || s === "tarde" || s === "sin_atender") resueltas++;
    }
    for (k = 0; k < this.pendientes.length; k++) if (this.pendientes[k].tipo === "emergencia") quedan = true;
    if (this.tick >= this.fin_tick || (resueltas === this.total && !quedan)) this._terminar();
  };
  C._terminar = function () {
    for (var k = 0; k < this.emergencias.length; k++) {
      var e = this.emergencias[k];
      if (e.estado !== "a_tiempo" && e.estado !== "tarde") e.estado = "sin_atender";
    }
    this.estado = "fin";
    this.eventos.push([this.tick, "fin", null]);
  };
  C.resumen = function () {
    var self = this, maximo = 0, bruto = 0, a_tiempo = 0, tarde = 0, resp = [], k;
    this.esc.eventos.forEach(function (e) { if (e.tipo === "emergencia") maximo += piso(self.m.gravedad[e.gravedad][1] * 5, 4); });
    for (k = 0; k < this.emergencias.length; k++) {
      var e = this.emergencias[k], base = this.m.gravedad[e.gravedad][1];
      if (e.estado === "a_tiempo") {
        a_tiempo++;
        var margen = Math.max(0, e.limite - e.entregada);
        bruto += base + piso(base * margen, 4 * Math.max(1, e.limite - e.aparece));
      } else if (e.estado === "tarde") { tarde++; bruto += piso(base, 5); }
      if (e.despachada >= 0) resp.push(e.despachada - e.aparece);
    }
    bruto -= 15 * (this.usados.despejar + this.usados.prioridad);
    bruto = Math.max(0, bruto);
    var suma = resp.reduce(function (x, y) { return x + y; }, 0), T = this.K.TICKS_S, rec = 0;
    for (k = 0; k < this.ambulancias.length; k++) rec += this.ambulancias[k].recorrido;
    return {score_raw: bruto, score_normalized: Math.min(1000, piso(bruto * 1000, Math.max(1, maximo))), a_tiempo: a_tiempo, tarde: tarde,
      sin_atender: this.total - a_tiempo - tarde, total: this.total, desvios: this.desvios,
      recursos: this.usados.despejar + this.usados.prioridad,
      respuesta_media_s: resp.length ? piso(piso(suma, resp.length) + piso(T, 2), T) : 0,
      recorrido_s: piso(rec, T), segundos: piso(this.tick, T), ordenes: this.ordenes.length};
  };
  C.exito = function () { var r = this.resumen(); return this.estado === "fin" && r.a_tiempo * 5 >= r.total * 3; };
  C.huella = function () {
    var h = [this.tick, this.estado, this.fase, this.camas.slice(), this.recursos.despejar, this.recursos.prioridad];
    this.ambulancias.forEach(function (a) { h.push([a.nodo, a.arista, a.prog, a.dur, a.estado, a.ruta.length, a.paciente]); });
    this.emergencias.forEach(function (e) { h.push(e.estado); });
    h.push(this.g.bloqueada.filter(function (b) { return b; }).length);
    return h;
  };

  var api = {Central: Central, Grafo: Grafo, Mapa: Mapa};
  if (typeof module === "object" && module.exports) module.exports = api; else raiz.CentralCivitas = api;
})(this);
