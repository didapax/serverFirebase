import json
import firebase_admin
from flask import Flask, request, jsonify
from firebase_admin import firestore, credentials

app = Flask(__name__)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def leer_archivo_json(ruta_archivo):
    try:
        with open(ruta_archivo, "r") as archivo:
            datos_json = json.load(archivo)
            return datos_json
    except FileNotFoundError:
        print(f"El archivo '{ruta_archivo}' no existe.")
        return None
    except json.JSONDecodeError:
        print(f"Error al decodificar el archivo JSON '{ruta_archivo}'.")
        return None
        

def update_clave_json(ruta_archivo, datos):
    try:
        with open(ruta_archivo, "w") as archivo:
            json.dump(datos, archivo, indent=4)
    except Exception as e:
        print(f"Error al guardar el archivo JSON: {e}")


def update_dic_json(ruta_archivo, datos):
    try:
        with open(ruta_archivo, "w") as archivo:
            json.dump(datos, archivo, indent=4)
    except Exception as e:
        print(f"Error al guardar el archivo JSON: {e}")


def agregar_datos_json(ruta_archivo, nuevos_datos):
    datos_json = leer_archivo_json(ruta_archivo)
    if datos_json is not None:
        datos_json.update(nuevos_datos)
        guardar_archivo_json(ruta_archivo, datos_json)


def agregar_elemento_lista_json(ruta_archivo, clave_lista="", nuevo_elemento):
    datos_json = leer_archivo_json(ruta_archivo)
    if datos_json is not None:
        if clave_lista:
            if clave_lista in datos_json and isinstance(datos_json[clave_lista], list):
                datos_json[clave_lista].append(nuevo_elemento)
            else:
                print(f"La clave '{clave_lista}' no existe o no es una lista.")
                return
        else:
            if isinstance(datos_json, list):
                datos_json.append(nuevo_elemento)
            else:
                print("El archivo JSON no contiene una lista en la raíz.")
                return

        update_dic_json(ruta_archivo, datos_json)
        

@app.route('/', methods=['GET', 'POST'])
def handle_requests():
    try:
        if request.method == 'GET':
            coleccion = request.args.get('coleccion', '')
            accion = request.args.get('accion', '')

            if coleccion:
                collection = db.collection(coleccion)
                try:
                    if accion == "lista":
                            resultados = []
                            for user_doc in collection.stream():
                                user_data = user_doc.to_dict()
                                user_data['id'] = user_doc.id  # Agrega el ID del documento al diccionario
                                resultados.append(user_data)

                            return jsonify(resultados)
                            
                    elif accion == "ver":
                            data_id = request.args.get('id', '')
                            doc_ref = collection.document(data_id)
                            documento = doc_ref.get()
                            if documento.exists:
                                datos = documento.to_dict()
                                json_data = json.dumps(datos)
                                parsed_data = json.loads(json_data)
                                return jsonify(parsed_data)
                            else:
                                return jsonify({'message': 'Documento no encontrado'})      
                            
                    elif accion == "where":
                        campo = request.args.get('campo', '')
                        valor = request.args.get('valor', '')
                        query = collection.where(campo, '==', valor)
                        resultados = query.stream()
                        lista = []  # Cambia 'resultados' a 'lista'
                        for doc in resultados:
                            datos = doc.to_dict()  # Cambia 'documento' a 'doc'
                            lista.append(datos)

                        json_data = json.dumps(lista)
                        parsed_data = json.loads(json_data)
                        return jsonify(parsed_data)                      
                          
                    else:
                        return jsonify({'message': 'No hay datos'})
                    
                except firestore.NotFound:
                    return jsonify({'message': 'error en el firestore'})

        elif request.method == 'POST':
            data = request.json
            coleccion = data.get('coleccion', '')
            accion = data.get('accion', '')

            if coleccion:
                collection = db.collection(coleccion)

                try:
                    if accion == "insert":
                        # Aquí va la lógica para el POST insert
                            data_id = data.get('id', '')
                            datos = data.pop("accion", None)
                            datos = data.pop("coleccion", None)
                            if data_id:
                                collection.document(data_id).set(data)
                            else:
                                collection.add(data)
                                
                            return jsonify({'message': 'Operación de inserción exitosa'})
                            
                    elif accion == "insert_many":
                        # Aquí va la lógica para el POST insert por lotes
                            data_id = data.get('id', '')
                            datos = data.pop("accion", None)
                            datos = data.pop("coleccion", None)
                            batch = db.batch()
                            if data_id:
                                batch.set(collection.document(data_id), data)
                            else:
                                batch.set(collection.document(), data)

                            return jsonify({'message': 'Operación de inserción por lote exitosa'})
                    
                    elif accion == "update":
                        # lógica para actualizar
                            data_id = data.get('id', '')
                            datos = data.pop("accion", None)
                            datos = data.pop("coleccion", None)
                            doc_ref = collection.document(data_id)
                            doc_ref.update(data)

                            return jsonify({'message': 'Operación de Actualizacion exitosa'})
                        
                    elif accion == "update[set]":
                        # lógica para actualizar y si el campo no existe lo crea
                            data_id = data.get('id', '')
                            datos = data.pop("accion", None)
                            datos = data.pop("coleccion", None)
                            doc_ref = collection.document(data_id)
                            doc_ref.set(data, merge=True)

                            return jsonify({'message': 'Operación de Actualizacion exitosa'})

                    elif accion == "update[query]":
                        # Otra lógica para actualizar segun un query
                            where = data.get('where', '')
                            datos = data.pop("accion", None)
                            datos = data.pop("coleccion", None)
                            datos = data.pop("where", None)
                            # Consulta los documentos con un campo específico
                            query = collection.where(where).get()
                            for doc in query:
                                doc.reference.update(data)                        

                            return jsonify({'message': 'Operación de Actualizacion exitosa'})

                    elif accion == "delete":
                        # Otra lógica para actualizar segun un query
                            data_id = data.get('id', '')
                            doc_ref = collection.document(data_id)                 
                            doc_ref.delete()
                            
                            return jsonify({'message': 'Eliminacion exitosa'})

                    elif accion == "delete[query]":
                        # Otra lógica para actualizar segun un query
                            where = data.get('where', '')
                            # Consulta los documentos con un campo específico
                            query = collection.where(where).get()
                            for doc in query:
                                doc.reference.delete()

                            return jsonify({'message': 'Operación de Eliminacion exitosa'})

                    else:
                        return jsonify({'error': 'Tipo de operación no válida'}), 400
                        
                except firestore.NotFound:
                    return jsonify({'message': 'error en el Firestore'}) 
        else:
            return jsonify({'error': 'No encuentra la página o recurso solicitado'}), 404
    except Exception as e:
        error_message = f"Error: {str(e)}"
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)

