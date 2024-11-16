# TODO:
# Timeline with usser occupation on projects
# Add "Add Deadline" button on project page
# Add DB automatic backup


from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
