# jwellery/context_processors.py
def wishlist(request):
    wishlist = request.session.get('wishlist', [])
    return {'wishlist': wishlist}
