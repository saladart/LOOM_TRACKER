# TODO:
# add logging
# fix deadline line in timeline
# Add DB automatic backup


from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
