---
title: "Privacidad"
description: "Qué registra phonometry.dev cuando lo lees: ninguna cookie, un aviso de visita propio, las peticiones que anota Cloudflare, cada campo que guarda cada uno y cuánto tiempo se conserva."
---

Este sitio no pone cookies, no muestra publicidad, no carga nada desde
servidores de otra empresa y no sigue a nadie de un sitio a otro. Sí cuenta las
visitas a las páginas y sí ve las peticiones, y esta página enumera cada campo
que se guarda, dónde y durante cuánto tiempo, para que puedas comprobar cada
afirmación contra el propio sitio.

## Quién lo gestiona

Yo: José Manuel Requena Plens, que mantengo phonometry (consulta
[Acerca de](/es/start/about/)). No hay empresa ni nadie más con acceso a estos
registros. Cloudflare sirve el sitio y procesa las peticiones por encargo mío;
cómo las trata Cloudflare lo describe su
[política de privacidad](https://www.cloudflare.com/privacypolicy/).

## Visitas a las páginas

Cuando una página termina de cargar, un pequeño script que lleva dentro envía
un único aviso a `/_v` en el propio phonometry.dev, nunca a otro servidor. El
aviso contiene la dirección de la página y los primeros 128 caracteres de su
query string, la página de procedencia (hasta 512 caracteres), cómo llegaste
(un enlace, una recarga, el botón de volver o una precarga), cuánto tardó en
cargar, el tamaño de tu pantalla, el de la ventana y la densidad de píxeles, el
idioma y la zona horaria del navegador, si el navegador declara que lo maneja
un programa automático y si la página era la de «no encontrada». No pone ninguna
cookie, no asigna ningún identificador y no guarda nada entre páginas, así que
no hay nada que pueda enlazar una visita con la siguiente ni seguirte a otro
sitio.

Ese aviso llega a un pequeño Worker mío en Cloudflare, que lo guarda como una
fila junto con lo que trae la propia petición: tu dirección IP, tu User-Agent
completo, los idiomas que acepta tu navegador, las cabeceras Sec-Fetch que envía
y lo que Cloudflare asocia a tu dirección (país, región, ciudad, código postal,
zona horaria, continente, coordenadas aproximadas y operador de red), además del
centro de datos de Cloudflare que respondió, el tiempo de ida y vuelta de tu
conexión y las versiones de HTTP y TLS usadas. Para frenar una avalancha,
Cloudflare cuenta además los avisos por dirección durante un minuto y descarta
los que pasan de 30; ese contador no se guarda en ningún sitio.

Las filas viven en un conjunto de datos de Cloudflare Analytics Engine que
Cloudflare conserva unos noventa días. Cada cinco minutos se copian a mi propia
base de datos de monitorización, donde se conservan un año y después se borran.
Cloudflare no guarda ningún registro de ejecución de este Worker: sus registros
están desactivados.

Estas cifras me dicen qué páginas se leen y cuáles responden «no encontrada»,
para saber qué mantener al día y qué arreglar. Es su único uso. No se cruzan con
nada más, no sirven para construir perfiles de lectores y no se comparten con
nadie.

## Peticiones

Cloudflare sirve todos los ficheros del sitio, así que ve todas las peticiones,
también las que no hace ningún navegador: los rastreadores y los agentes que
leen las copias en Markdown, los ficheros llms y los sitemaps no ejecutan
ningún script ni envían aviso de visita. Para sus propias analíticas,
Cloudflare anota de cada petición la hora, tu dirección IP, la ruta y la query
pedidas, el User-Agent, la red y el país de origen, el método y el estado de la
respuesta (Cloudflare los conserva 31 días). Cada cinco minutos, los registros
de los ficheros que leen los agentes (las copias en Markdown, los ficheros llms,
los sitemaps, robots.txt y los ficheros de `/.well-known/`) se copian a la misma
base de datos de monitorización que las visitas, donde se conservan un año y
después se borran, para que pueda ver qué ficheros piden los rastreadores.

## Cookies y almacenamiento

Ninguna respuesta de este sitio lleva la cabecera `Set-Cookie`. Lo que el sitio
guarda en tu dispositivo es poco, y nada de ello se envía nunca a ningún sitio:

- en `localStorage`, tu tema de color, tu idioma cuando eliges uno, el hecho de
  que cerraste la sugerencia de cambiar de idioma y qué pestaña elegiste en un
  grupo de pestañas (por ejemplo `pip` o `conda`), para que la misma pestaña se
  abra en la página siguiente;
- en `sessionStorage`, solo mientras la pestaña está abierta, el estado de la
  navegación lateral.

La sugerencia de leer una página en el otro idioma compara los idiomas que
anuncia tu navegador con el de la página, todo dentro de tu navegador.

## Otros servidores

Todo lo que carga una página viene de phonometry.dev o, en el caso de los
vídeos, de media.phonometry.dev, el servidor propio del sitio para ellos. Una
Content Security Policy obliga a las páginas a ello: scripts, estilos, fuentes
e imágenes solo se aceptan de este origen. El buscador funciona en tu
navegador: su índice se descarga de este sitio y lo que escribes no se envía a
ningún sitio.

Si tu navegador bloquea algo de una página (una infracción de la Content
Security Policy), puede enviar un breve informe con la dirección de la página,
la de procedencia y el recurso bloqueado a `jmrp.io/csp-report`, mi propio
servidor, donde se trata como describe la
[página de privacidad de jmrp.io](https://jmrp.io/es/privacy/). Esos informes
existen para que una página rota se detecte el mismo día.

Un enlace a otro sitio (GitHub, PyPI, el editor de una norma) te lleva a ese
sitio, y a partir de ahí se aplica su propia política.

## Señales que envía tu navegador

[`/.well-known/gpc.json`](/.well-known/gpc.json) declara que este sitio respeta
Global Privacy Control. Aquí no se vende ni se comparte nada con fines
publicitarios, así que la señal no tiene nada que desactivar; el fichero lo
dice en la forma que un navegador puede leer.

## Sin publicidad ni afiliados

No hay publicidad, enlaces de afiliado, contenido patrocinado ni lista de
correo. La [página de apoyo](/es/start/support/) enumera formas de ayudar al
proyecto; sus enlaces son enlaces normales que no ponen nada ni miden nada.

## Tus datos

Puedes pedirme qué se guarda sobre ti o pedirme que lo borre. Aquí nada guarda
un nombre ni una cuenta, así que para encontrar tus filas necesito la dirección
IP que usaste y más o menos cuándo. Escribe a `mail@jmrp.io`. Los informes de
seguridad tienen su propio canal:
[`/.well-known/security.txt`](/.well-known/security.txt) y la
[política de seguridad](https://github.com/jmrplens/phonometry/security/policy)
del proyecto.
