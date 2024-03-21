from sanic_openapi import doc


class UsersModels:
    first_name = doc.String()
    last_name = doc.String()
    middle_name = doc.String()
    username = doc.String()
    password = doc.String()
    photo = doc.String()
    birthday = doc.Date()


class DistrictsModels:
    title = doc.String()
    region_id = doc.Integer()


class RegionsModels:
    title = doc.String()
    number = doc.Integer()


class TracksModels:
    title = doc.String()
    description = doc.String()
    district_id = doc.Integer()


class TrafficsModels:
    title = doc.String()
    description = doc.String()
    track_id = doc.Integer()
    video_path = doc.String()
    counters = doc.Dictionary(description='counts car, truck, bus')
    status = doc.Integer(description='-1: delete; 0: in queue; 1: in progress; 2: success done; 3: error done')


class UsersLoginModels:
    username = doc.String()
    password = doc.String()
