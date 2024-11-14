# TODO:
# Remove User and Remove Project
# Some simple design with dark theme and LOOM logo
# Timeline with usser occupation on projects
# Add export options for aggreagation data
# Add table view for admin for db entries


from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
