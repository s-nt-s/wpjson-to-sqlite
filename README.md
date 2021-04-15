Crea una base de datos sqlite obteniendo contenido desde la api de wordpress.

```console
$ ./wp2db.py --help
usage: wp2db.py [-h] [--out OUT] [--subdom] [--tags] [--media] [--comments]
                [--excluir [EXCLUIR [EXCLUIR ...]]]
                [url [url ...]]

Crea una base de datos sqlite con el contendio de un wordpress

positional arguments:
  url                   URL del wordpress

optional arguments:
  -h, --help            show this help message and exit
  --out OUT             Fichero de salida
  --subdom              Cargar tambien subdominos
  --tags                Guardar tags
  --media               Guardar media
  --comments            Guardar comentarios
  --excluir [EXCLUIR [EXCLUIR ...]]
                        Excluir post/page de algún dominio. Formato
                        web:id1,id2 o web si se excluye por completo
```

# Ejemplos

## Descargar un blog wordpress

```$ ./wp2db.py https://wpexample.net/
>>> titulo_wpexample.db

wpexample.net
    4 posts
    2 pages
    1 users
    2 categories
Creando sqlite 100%

Tamaño: 36.0KB
```

`./wp2db.py wpexample.net` da el mismo resultado.

## Descargar un blog wordpress y todos sub-blogs encontrados

Primero descarga el blog pasado por parámetro y luego inspecciona
los enlaces encontrados en `posts` y `pages` con fin de encontrar
subdominios que puedan ser blogs wordpress y así descargarlos también.


```$ ./wp2db.py --subdom https://wpexample.net/
>>> titulo_wpexample.db

wpexample.net
    4 posts
    2 pages
    1 users
    2 categories
Creando sqlite 100%

sub1.wpexample.net
    6 posts
    3 pages
    1 users
    2 categories
Creando sqlite 100%

sub2.wpexample.net
    8 posts
    4 pages
    6 users
    2 categories
Creando sqlite 100%

Tamaño: 56.0KB
```

`./wp2db.py --subdom wpexample.net` da el mismo resultado.

## Excluir página o post problematico

En algunas ocasiones el servidor que alberga el blog wordpress
contiene algún error que imposibilita la obtención de una página o post,
para evitar que este error imposiblilite al script continuar podemos
usar el comando `--excluir` que acepta como parámetro dominios e ids de
post/page, por ejemplo `./wp2db.py --excluir wpexample.net:484 wpexample.net`
evitara pedir a la api wordpress la post/page 484
