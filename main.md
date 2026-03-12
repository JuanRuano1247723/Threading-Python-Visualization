Claro, aquí tienes la tabla convertida a formato Markdown:

| Modo                 | Primitiva                | Cómo se usa                                                                                |
| :------------------- | :----------------------- | :----------------------------------------------------------------------------------------- |
| Semáforo             | `threading.Semaphore(N)` | Cada hilo hace acquire()/release(). Si no hay permisos, el hilo realmente se bloquea       |
| Mutex                | `threading.Lock()`       | Solo 1 hilo puede tener el lock. Los demás bloquean en acquire()                           |
| Monitor              | `threading.Condition()`  | Hilos hacen wait()/notify(). La condición gestiona automáticamente el acceso               |
| Sección Crítica      | `threading.Lock()`       | Con protección: hilos usan el lock. Sin protección: lo ignoran → múltiples en zona = error |
| Condición de Carrera | Ninguna                  | Dos hilos corren al mismo punto SIN sincronización → colisión                              |
| Deadlock             | 2x `threading.Lock()`    | H1 adquiere lock_h, intenta lock_v. H2 adquiere lock_v, intenta lock_h → deadlock real     |
| Concurrencia         | `threading.Thread` x6    | 6 hilos independientes, cada uno en su carril                                              |
