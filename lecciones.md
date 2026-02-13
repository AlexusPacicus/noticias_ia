Lecciones técnicas aprendidas (v1)
1. El nivel importa más que el contenido
Un mismo concepto (aborts, errores, validación) cambia completamente según el nivel:
Sistema → clases de invalidez.
Nodo → casuística concreta.
Bajar de nivel demasiado pronto rompe el diseño.
2. No todo “contrato” es ejecutable
Un contrato puede ser:
operativo (MAF),
o gobernanza humana (este sistema).
Forzar ejecutabilidad prematura empeora la arquitectura.
3. El contrato correcto evita decisiones futuras
Un buen contrato no dice “qué hacer”, dice:
qué no está permitido decidir más adelante.
El valor está en el alcance negativo, no en el positivo.
4. Abortar es una herramienta de diseño, no de runtime
En fases tempranas:
ABORT ≠ fallo.
ABORT = señal de límite no gobernado.
Intentar “salvar” ejecuciones introduce semántica implícita.
5. Artefactos exógenos clarifican gobernanza
Separar explícitamente:
input del usuario
configuración del sistema
dependencias externas
reduce ambigüedad y drift.
6. Una sola fuente acelera aprendizaje arquitectónico
En v1:
más fuentes ≠ más señal,
más fuentes = más ruido estructural.
Reducir variables mejora diseño, no lo empobrece.
7. Determinismo es una propiedad de sistema, no de nodos
No se “arregla” en un punto.
Se impone globalmente con:
orden fijo,
decisiones inmutables,
artefactos versionados.
8. LLM ≠ ML decisional
Usar LLM como:
transformador de texto → aceptable.
fuente de criterio → rompe gobernanza.
Declarar prescindibilidad del LLM es una prueba de diseño sano.
9. Tests son gates de diseño, no solo de código
En sistemas contractuales:
un test fallido invalida la versión, no solo el commit.
avanzar sin pasar gates crea deuda arquitectónica.
10. El malestar suele indicar un error de abstracción
Cuando algo “no encaja”:
no suele ser la regla,
suele ser el nivel en el que la estás definiendo.
Detectar eso a tiempo es madurez técnica.
11. README ≠ documentación blanda
Un README de gobernanza:
fija decisiones,
evita reinterpretaciones,
permite auditar el pasado.
Es una herramienta de ingeniería, no marketing.

12. Los aborts generales invalidan el flujo, no la ejecución
Un abort general no detiene runtime ni gestiona errores. Define cuándo un flujo no puede considerarse una referencia válida, aunque ejecute y produzca outputs.
13. Un abort general solo existe si obliga a rediseñar
Si una condición puede resolverse con más lógica, validaciones o código defensivo, no es un abort general. Los aborts señalan límites sistémicos, no deficiencias de implementación.
14. Las clases de invalidez se definen arriba; las manifestaciones, abajo
Los contratos específicos pueden declarar causas concretas solo como especializaciones explícitas de un abort general. Nunca crean clases nuevas.
15. La inferencia implícita es una forma de no determinismo
Depender de supuestos no contractuales rompe el determinismo estructural, aunque el sistema sea estable en la práctica.
16. Determinismo y auditabilidad no son equivalentes
Un flujo puede ser determinista y aun así no ser validable ex-post. La auditabilidad es una propiedad independiente que debe protegerse explícitamente.
17. El LLM solo es aceptable cuando es prescindible
Si el flujo no puede justificarse sin el LLM, este ha asumido criterio. Declarar explícitamente qué transformaciones textuales están permitidas es clave.
18. Redundancia en aborts indica mal nivel de abstracción
Cuando dos aborts se solapan, normalmente uno pertenece a una clase más general. Consolidar mejora claridad y gobernanza.
19. Los aborts generales deben definirse antes que los específicos
Invertir el orden produce excepciones ad-hoc y drift semántico. Los aborts específicos emergen solos al escribir contratos de nodo.


Lecciones Chat contrato State:

P1. Separación de planos
Nunca mezclar existencia, temporalidad y semántica en el mismo nivel contractual.
Primero qué existe, luego cuándo, nunca por qué.
P2. El State gobierna permisos, no significado
El State define quién puede leer/escribir, no qué representa el dato ni cómo se usa.
P3. Dependencias explícitas > dependencias implícitas
Toda lectura debe estar listada explícitamente.
Una dependencia no declarada es una violación, no un detalle de implementación.
P4. Eliminar estado intermedio mejora gobernanza
Si un dato no es estrictamente necesario como estado, debe vivir solo en el output final.
P5. Configuración ≠ estado
Artefactos exógenos y settings nunca forman parte del State, aunque condicionen el resultado.
P6. “Todos” es una decisión, no un atajo
Cualquier comodín semántico debe declararse y justificarse como excepción contractual.
P7. El State se congela antes que los nodos
Sin State FROZEN, los contratos específicos no son estables ni auditables.
P8. No prometas lo que no defines
Si un contrato menciona tipos, niveles o reglas, deben existir explícitamente o no mencionarse.


Lecciones aprendidas (hasta validate_input)
La incomodidad es una señal válida de diseño
Si un nodo “cumple” pero no resulta elegante, suele haber una mezcla semántica latente (p. ej. validar vs decidir defaults).
Validar ≠ decidir
La validación pertenece a la frontera; la aplicación de defaults es política de sistema. Mezclarlas es aceptable en v1, pero conceptualmente impuro.
Los defaults son una excepción, no una norma
Si un nodo aplica defaults, debe declararse explícitamente como excepción contractual, no como comportamiento implícito.
Isomorfismo documental no es estética, es gobernanza
Todos los contratos de nodo deben compartir exactamente los mismos apartados y orden. Facilita auditoría, lectura cruzada y consistencia mental.
Un nodo bien definido deja una única huella observable
Si la corrección de un nodo no puede evaluarse mirando solo su output (o abort), el nodo tiene efectos colaterales indebidos.
La escritura debe ser atómica o no existir
O se escribe un artefacto completo y válido, o se aborta. No hay estados intermedios contractuales.
“No leer State” incluye no leer indirectamente
Prohibir lecturas no solo significa “no otros campos”, sino también no acceder a config, reloj, entorno o artefactos externos.
Los aborts describen invalidez, no errores operativos
Un abort no implica bug: implica que el sistema, como referencia gobernada, no es válido bajo ese input.
Si algo cuesta justificar por escrito, probablemente está mal colocado
El esfuerzo excesivo en explicar una responsabilidad suele indicar que debería vivir en otro nodo.
La frontera de entrada es sagrada
Si validate_input se debilita, el resto del sistema deja de ser gobernable, aunque “funcione”.
La redundancia contractual puede ser intencional como mecanismo de enforcement local, siempre que sea trazable 1:1 al contrato general y se revise antes del freeze.


Lecciones aprendidas — Nodo fetch y nodos sucios
1. No todos los contratos se diseñan igual
Existen contratos axiomáticos (gobernanza, State, frontera) y contratos empíricamente condicionados (fetch, normalización, decisión). Forzar el mismo proceso a ambos genera contratos frágiles.
2. Un contrato de nodo sucio sin fricción empírica es incompleto
Los nodos que interactúan con el mundo real no pueden cerrarse a priori. La fricción con datos reales no valida el contrato: lo informa.
3. Los datos sirven para descubrir límites, no para adaptar el contrato
Probar con datos reales no tiene como objetivo “hacer que pase”, sino identificar:
supuestos falsos,
decisiones implícitas,
y puntos que deben abortar o declararse fuera de alcance.
4. Los nodos sucios se diseñan de uno en uno
Probar el pipeline completo introduce ruido cruzado.
La secuencia correcta es: aislar nodo → chocar con pocos casos → cerrar contrato → congelar.
5. fetch es el primer punto donde el determinismo debe ceder
El determinismo inter-ejecución no es exigible en nodos de frontera externa. Lo que sí debe garantizarse es:
aislamiento,
ausencia de criterio,
y trazabilidad contractual.
6. El orden no contractual es una decisión de diseño
No declarar garantías de orden en fetch evita arrastrar no-determinismo implícito a nodos posteriores. El caos debe admitirse explícitamente donde nace.
7. Un abort no siempre es técnico: puede ser político
Abortar ante respuesta vacía (FETCH_EMPTY_RESPONSE) no es un error de implementación, sino una decisión de alcance de versión. Declararlo evita parches posteriores.
8. El contrato debe cerrar puertas, no explicar intenciones
Cualquier frase explicativa, pedagógica o meta (“manténlo seco”, “no hay que inventar nada”) no pertenece al contrato. El contrato solo define permisos, prohibiciones y consecuencias.
9. El valor del contrato está en lo que prohíbe
Un buen contrato de nodo sucio no describe qué hacer con datos malos; describe qué está prohibido decidir en ese nodo.
10. Un contrato está listo cuando puede romperse
Un contrato en DRAFT es válido cuando puede enfrentarse a datos reales sin reinterpretarse. Si necesita explicación oral para sostenerse, aún no está cerrado.


Lecciones técnicas
La evidencia empírica sirve para decidir contratos, no para documentarse.
Observas → ajustas → borras.
Un abort es válido aunque no sea observable en una fuente concreta.
FETCH_EMPTY_RESPONSE es política de sistema, no propiedad de arXiv.
Error envuelto ≠ empty.
Payload legible con “Error” explícito → FETCH_SOURCE_ERROR.
Timeout = fallo de fuente, no caso límite lógico.
No todo XML válido es transportable.
Transportable = colección iterable sin interpretación.
No fuerces a una fuente a confirmar una hipótesis.
Si deriva a error repetidamente, se acepta la limitación empírica.
Lecciones de diseño contractual
El State manda.
Un rename (external_units) mal alineado invalida un nodo entero.
Aborts deben mapear 1:1 a casos observados o decisiones explícitas.
Separar “frontera sucia” del sistema gobernado es clave.
fetch contiene el caos; el resto no lo hereda.
Freeze solo cuando el grafo completo esté cerrado.
No congelar nodos aislados “por impulso”.
Lecciones de repo / disciplina
El repo no es un cuaderno de laboratorio.
Solo queda lo contractual y lo productivo.
Snapshots parciales son ruido.
O set completo o ninguno.
Scripts de probe no son parte del sistema.
Útiles localmente, fuera del repo.