class MascotaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                mascota = getattr(request.user, 'mascota', None)
                if mascota:
                    mascota.actualizar_hambre()
            except:
                # Ignora errores relacionados con mascota
                pass
        return self.get_response(request)