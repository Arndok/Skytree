# Skytree
2D game framework for Python
Version 0.1

# Features
Skytree is a general 2D game engine that can be used as a Python package.
It requires Pygame to work, and has been tested with Python 3.11 / Pygame 2.6

Skytree uses Pygame to render 2D graphics, play audio and read user inputs. At the moment, only keyboard inputs are supported.
The engine abstracts the game loop from the user, provides a standard structure for active game objects and a way to manage game resources.
Objects are generally constructed by combining basic features (Drawable, Updateable, etc) via multiclass and are connected or disconnected
ultimately to a game manager singleton object in order to make them active or inactive.
Drawable objects provide methods to manipulate their draw order and alignment, and there is a frame-by-frame animation system.
Skytree features a collision detection-response system with support for different shaped hitboxes.
User inputs are translated to string commands that can be interpreted by the game objects.
There is a system of classes dedicated to modeling game entities and spaces, with a focus on sidescrolling platformers.

# Instrucciones para el consultor (entrega PEC2)
Vídeo explicativo sobre el motor en https://www.youtube.com/watch?v=P-MAbDhIuok

INSTRUCCIONES DE INSTALACIÓN Y USO PARA LA DEMO JUGABLE:
- Opción A (ejecutable para Windows; probado en Windows 10): 
  - Descargar el archivo Skytree Demo.zip
  - Descomprimir y ejecutar demo.exe
- Opción B (paquete de Python; probado con Python 3.11 y Pygame 2.6)
  - Descargar e instalar Python 3.11 desde https://www.python.org/downloads/
  - Descargar e instalar Pygame 2.6. Se puede instalar desde pip siguiendo las instrucciones en https://www.pygame.org/wiki/GettingStarted
  - Descargar el script demo.py y las carpetas /skytree y /demo_resources
  - Ejecutar demo.py

Características en la demo:
- Renderizado de gráficos 2D; reproducción de música y sonidos.
- Estado de pausa que permite salir de una fase al mapa, o bien cerrar el juego desde el mapa.
- Mapa: estado modificable y persistente; jugador con movimiento por casillas.
- Fase 1: pantalla simple con un personaje jugador con movimiento omnidireccional.
- Fase 2: características para juegos de plataformas con vista lateral; opciones para configurar y conectar los espacios; sistema de capas con posibilidad de configurar objetos por casillas; personaje jugador que puede saltar y agacharse, diferentes entidades enemigas y objetos generadores de entidades; sistema de puntos de control (se puede salir de la fase mediante el estado de pausa y volver a entrar manteniendo el último punto de control activado).
- Fase 3: clon de Pang; colisiones entre círculos y rectángulos; uso de clases nuevas en el script: personaje jugador con puntos de vida y disparo comprometido, entidades que generan otras entidades y que construyen sus atributos de manera dinámica a partir de un factor de tamaño.
- Controles:
  - Los personajes se mueven con WASD o las flechas. El personaje jugador de vista lateral puede saltar con A / arriba y agacharse con S / abajo. 
  - Enter para entrar en las fases.
  - ESC para activar el estado de pausa.
  - Espacio para disparar en la fase 3.
