import re

" configuracion del sistema "
TIPOS_PERMITIDOS = {"CARGA", "RESERVADO", "COMPACTO", "GRANDE", "MOTO"}

COMANDOS_VALIDEZ = {
    "REGISTRAR": 2,
    "ASIGNAR": 1,
    "LLEGADA": 1,
    "AUTORIZAR_SALIDA": 1,
    "SALIDA": 1,
    "APAGAR_ALARMA": 1,
    "CONSULTAR": 0
}

PLACA_RE = re.compile(r"^[A-Z0-9]{6,7}$")

TOKEN_RE = re.compile(
    r"\s*(?:(?P<WORD>[A-Z_][A-Z0-9_]*)|"
    r"(?P<LPAREN>\()|"
    r"(?P<RPAREN>\))|"
    r"(?P<COMMA>,)|"
    r"(?P<NUMBER>[0-9]+)|"
    r"(?P<SKIP>\s+)|"
    r"(?P<OTHER>.))"
)


"Lexer"
def lexer(texto_instruccion):
    tokens = []
    posicion = 0
    texto_instruccion = texto_instruccion.upper()
    
    while posicion < len(texto_instruccion):
        coincidencia = TOKEN_RE.match(texto_instruccion, posicion)
        if not coincidencia:
            raise ValueError("Error Léxico: Carácter no reconocido.")
        
        posicion = coincidencia.end()
        grupo = coincidencia.lastgroup
        valor = coincidencia.group().strip()

        if grupo == "SKIP" or not valor:
            continue
        elif grupo in ("WORD", "NUMBER"):
            tokens.append(("WORD", valor))
        elif grupo == "LPAREN":
            tokens.append(("LPAREN", "("))
        elif grupo == "RPAREN":
            tokens.append(("RPAREN", ")"))
        elif grupo == "COMMA":
            tokens.append(("COMMA", ","))
        else:
            raise ValueError(f"Error Léxico: Carácter no permitido '{valor}'.")
            
    tokens.append(("EOF", ""))
    return tokens


"Parser"
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0

    def actual(self):
        return self.tokens[self.posicion]

    def consumir(self, tipo_esperado):
        token_actual = self.actual()
        if token_actual[0] != tipo_esperado:
            raise ValueError(f"Error Sintáctico: Se esperaba '{tipo_esperado}' y se recibió '{token_actual[0]}'.")
        self.posicion += 1
        return token_actual[1]

    def parsear(self):
        nombre_comando = self.consumir("WORD")
        if nombre_comando not in COMANDOS_VALIDEZ:
            raise ValueError(f"Error Sintáctico: Comando desconocido '{nombre_comando}'.")

        self.consumir("LPAREN")
        argumentos = []
        cantidad_esperada = COMANDOS_VALIDEZ[nombre_comando]

        if cantidad_esperada > 0:
            argumentos.append(self.consumir("WORD"))
            if cantidad_esperada == 2:
                self.consumir("COMMA")
                argumentos.append(self.consumir("WORD"))

        self.consumir("RPAREN")

        if self.actual()[0] != "EOF":
            raise ValueError("Error Sintáctico: Símbolos no reconocidos tras el paréntesis final.")

        return nombre_comando, argumentos


"Simulacion H"
class ControlHardware:
    def cambiar_estado_led(self, id_espacio, ocupado):
        color = "ROJO" if ocupado else "VERDE"
        print(f"[HARDWARE]: LED de espacio {id_espacio} cambia a -> {color}")




class SistemaParqueo:
    def __init__(self):
        self.hardware = ControlHardware()
        
        "espacios del parqueo fisicos disponibles"
        self.espacios = {
            "C-01": {"tipo": "CARGA", "ocupado": False, "vehiculo": None},
            "R-01": {"tipo": "RESERVADO", "ocupado": False, "vehiculo": None},
            "K-01": {"tipo": "COMPACTO", "ocupado": False, "vehiculo": None},
            "G-01": {"tipo": "GRANDE", "ocupado": False, "vehiculo": None},
            "M-01": {"tipo": "MOTO", "ocupado": False, "vehiculo": None},
        }

       
        self.vehiculos = {}

    def _validar_placa(self, placa):
        if not PLACA_RE.fullmatch(placa):
            raise ValueError(f"Error Semántico: Placa '{placa}' inválida. Debe ser de 6 a 7 caracteres alfanuméricos.")

    def ejecutar(self, texto_comando):
        tokens = lexer(texto_comando)
        comando, argumentos = Parser(tokens).parsear()

        if comando == "REGISTRAR":
            return self._cmd_registrar(argumentos[0], argumentos[1])
        elif comando == "ASIGNAR":
            return self._cmd_asignar(argumentos[0])
        elif comando == "LLEGADA":
            return self._cmd_llegada(argumentos[0])
        elif comando == "AUTORIZAR_SALIDA":
            return self._cmd_autorizar_salida(argumentos[0])
        elif comando == "SALIDA":
            return self._cmd_salida(argumentos[0])
        elif comando == "APAGAR_ALARMA":
            return self._cmd_apagar_alarma(argumentos[0])
        elif comando == "CONSULTAR":
            return self._cmd_consultar()

    def _cmd_registrar(self, tipo, placa):
        if tipo not in TIPOS_PERMITIDOS:
            raise ValueError(f"Error Semántico: Tipo '{tipo}' inválido. Permitidos: {TIPOS_PERMITIDOS}")
        self._validar_placa(placa)
        if placa in self.vehiculos:
            raise ValueError(f"Error Semántico: La placa {placa} ya existe en el registro.")

        self.vehiculos[placa] = {
            "tipo": tipo,
            "espacio_asignado": None,
            "estado": "REGISTRADO",
            "salida_autorizada": False,
            "alarma_activa": False
        }
        return f"OK: Vehículo {placa} registrado exitosamente como {tipo}."

    def _cmd_asignar(self, placa):
        self._validar_placa(placa)
        if placa not in self.vehiculos:
            raise ValueError(f"Error Semántico: La placa {placa} no existe en el sistema.")

        vehiculo = self.vehiculos[placa]
        if vehiculo["espacio_asignado"] is not None:
            raise ValueError(f"Error Semántico: La placa {placa} ya tiene el espacio {vehiculo['espacio_asignado']}.")

        espacio_libre = None
        for id_e, datos in self.espacios.items():
            if datos["tipo"] == vehiculo["tipo"] and not datos["ocupado"] and datos["vehiculo"] is None:
                espacio_libre = id_e
                break

        if not espacio_libre:
            raise ValueError(f"Error Semántico: No hay espacios libres para el tipo {vehiculo['tipo']}.")

        self.espacios[espacio_libre]["vehiculo"] = placa
        vehiculo["espacio_asignado"] = espacio_libre
        vehiculo["estado"] = "ASIGNADO"
        return f"OK: Espacio {espacio_libre} asignado a la placa {placa}."

    def _cmd_llegada(self, placa):
        self._validar_placa(placa)
        if placa not in self.vehiculos:
            raise ValueError(f"Error Semántico: La placa {placa} no existe.")

        vehiculo = self.vehiculos[placa]
        if vehiculo["espacio_asignado"] is None:
            raise ValueError(f"Error Semántico: La placa {placa} no tiene espacio asignado.")

        id_e = vehiculo["espacio_asignado"]
        self.espacios[id_e]["ocupado"] = True
        vehiculo["estado"] = "EN_PARQUEO"
        
        self.hardware.cambiar_estado_led(id_e, ocupado=True)
        return f"OK: Llegada confirmada para {placa} en espacio {id_e}."

    def _cmd_autorizar_salida(self, placa):
        self._validar_placa(placa)
        if placa not in self.vehiculos:
            raise ValueError(f"Error Semántico: La placa {placa} no existe.")

        vehiculo = self.vehiculos[placa]
        if vehiculo["estado"] != "EN_PARQUEO":
            raise ValueError(f"Error Semántico: El vehículo {placa} no está actualmente dentro del parqueo.")

        vehiculo["salida_autorizada"] = True
        return f"OK: Salida autorizada para la placa {placa}."

    def _cmd_salida(self, placa):
        self._validar_placa(placa)
        if placa not in self.vehiculos:
            raise ValueError(f"Error Semántico: La placa {placa} no existe.")

        vehiculo = self.vehiculos[placa]
        id_e = vehiculo["espacio_asignado"]

        if not vehiculo["salida_autorizada"]:
            vehiculo["alarma_activa"] = True
            self.hardware.activar_alarma(id_e, placa)
            raise ValueError(f"ALERTA SEGURIDAD: Intentó salir sin autorización. Alarma disparada para {placa}.")

        if id_e in self.espacios:
            self.espacios[id_e]["ocupado"] = False
            self.espacios[id_e]["vehiculo"] = None
            self.hardware.cambiar_estado_led(id_e, ocupado=False)

        del self.vehiculos[placa]
        return f"OK: Vehículo {placa} retirado. Espacio {id_e} liberado."

    def _cmd_apagar_alarma(self, placa):
        self._validar_placa(placa)
        if placa not in self.vehiculos:
            raise ValueError(f"Error Semántico: La placa {placa} no existe.")

        self.vehiculos[placa]["alarma_activa"] = False
        self.hardware.desactivar_alarma(placa)
        return f"OK: Alarma apagada correctamente para {placa}."

    def _cmd_consultar(self):
        lineas = ["\nESTADO ACTUAL DEL PARQUEO", "-------------------------", "ESPACIOS:"]
        for id_e, datos in self.espacios.items():
            estado_str = "OCUPADO" if datos["ocupado"] else "LIBRE"
            vehiculo_str = f"({datos['vehiculo']})" if datos["vehiculo"] else "(Vacio)"
            lineas.append(f"  Espacio {id_e} [{datos['tipo']}]: {estado_str} {vehiculo_str}")

        lineas.append("\nVEHICULOS:")
        if not self.vehiculos:
            lineas.append("  (Sin vehiculos registrados)")
        else:
            for placa, info in self.vehiculos.items():
                espacio = info['espacio_asignado'] if info['espacio_asignado'] else "Sin asignar"
                lineas.append(f"  Placa: {placa} | Tipo: {info['tipo']} | Estado: {info['estado']} | Espacio: {espacio}")

        return "\n".join(lineas)



if __name__ == "__main__":
    parqueo = SistemaParqueo()

 
    print(" Sistema de Parqueo")


    while True:
        try:
            linea = input("\n[LENGUAJE FORMAL] > ").strip()
            if not linea:
                continue
            if linea.upper() == "SALIR":
                print("Cerrando la consola de control...")
                break

            resultado = parqueo.ejecutar(linea)
            print(f"[RESPUESTA SISTEMA]: {resultado}")

        except ValueError as err:
            print(f"[ERROR DETECTADO]: {err}")
        except KeyboardInterrupt:
            print("\nConsola finalizada.")
            break