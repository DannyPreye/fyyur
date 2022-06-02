#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import json
import sys
from tkinter import S
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, session, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import all_
from forms import *
from flask_migrate import Migrate
from datetime import date, datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Shows(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"start time{self.start_time}"


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    looking_for_talent = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String())
    genres = db.Column(db.String(120))
    venue = db.relationship('Venue', secondary=Shows.__tablename__,
                            backref=db.backref('Venue_shows', lazy=True))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

    def __repr__(self):
        return f"Venue Name{self.name} Venue City{self.city}"


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    looking_for_venue = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String())
    artists = db.relationship('Artist', secondary=Shows.__tablename__,
                              backref=db.backref('Artist_shows', lazy=True))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

    def __repr__(self):
        return f"Artist Name{self.name}"

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = Venue.query.all()

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search = request.form.get('search_term', '')
    venue = Venue.query.filter(Venue.name.ilike(f"%{search}%")).all()
    response = {
        "count": Venue.query.filter(Venue.name.ilike(f"%{search}%")).count(),
        "data": venue
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    today_date = date.today()
    past_shows = db.session.query(Shows, Artist).join(
        Artist).filter(Artist.id == Shows.artist_id, Shows.start_time < today_date, Shows.venue_id == venue_id).all()
    upcomming_shows = db.session.query(Shows, Artist).join(
        Artist).filter(Artist.id == Shows.artist_id, Shows.start_time > today_date, Shows.venue_id == venue_id).all()

    venue = {
        "venue": Venue.query.get(venue_id),
        "past_shows":  past_shows,
        "upcoming_shows": upcomming_shows,
        "past_shows_count":  db.session.query(Shows, Artist).join(
            Artist).filter(Artist.id == Shows.artist_id, Shows.start_time < today_date, Shows.venue_id == venue_id).count(),
        "upcoming_shows_count":  db.session.query(Shows, Artist).join(
            Artist).filter(Artist.id == Shows.artist_id, Shows.start_time > today_date, Shows.venue_id == venue_id).count()
    }

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    form = VenueForm()
    try:
        check = False
        if request.form.get('seeking_talent') == 'y':
            check = True
        venue = Venue(
            name=request.form.get("name"),
            city=request.form.get("city"),
            state=request.form.get("state"),
            address=request.form.get("address"),
            phone=request.form.get("phone"),
            image_link=request.form.get("image_link"),
            facebook_link=request.form.get("facebook_link"),
            website_link=request.form.get("website_link"),
            looking_for_talent=check,
            description=request.form.get("seeking_description"),
            genres=request.form.getlist("genres")
        )
        db.session.add(venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        flash('Venue was ' + request.form['name'] + ' successfully listed!')

    else:
        flash('An error occurred. Venue ' +
              request.form["name"] + ' could not be listed.')

    return render_template('pages/home.html')
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    # on successful db insert, flash success
    # flash('Venue was' + request.form.get('name') + 'successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search = request.form.get('search_term', '')
    artist = Artist.query.filter(Artist.name.ilike(f"%{search}%")).all()
    response = {
        "count": Artist.query.filter(Artist.name.ilike(f"%{search}%")).count(),
        "data": artist
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id

    today_date = date.today()
    past_shows = db.session.query(Shows, Venue).join(
        Venue).filter(Venue.id == Shows.venue_id, Shows.start_time < today_date, Shows.artist_id == artist_id).all()
    upcomming_shows = db.session.query(Shows, Venue).join(
        Venue).filter(Venue.id == Shows.venue_id, Shows.start_time > today_date, Shows.artist_id == artist_id).all()
    print(past_shows)
    artist = {
        "artist": Artist.query.get(artist_id),
        "past_shows":  past_shows,
        "upcoming_shows": upcomming_shows,
        "past_shows_count":  db.session.query(Shows, Venue).join(
            Venue).filter(Venue.id == Shows.venue_id, Shows.start_time < today_date, Shows.artist_id == artist_id).count(),
        "upcoming_shows_count":  db.session.query(Shows, Venue).join(
            Venue).filter(Venue.id == Shows.venue_id, Shows.start_time > today_date, Shows.artist_id == artist_id).count()
    }

    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    error = False
    try:
        artist = Artist.query.get(artist_id)
        print("artist", artist.name)
        check = False
        if request.form.get('seeking_talent') == 'y':
            check = True
        artist.name = request.form.get('name')
        artist.city = request.form.get('city')
        artist.state = request.form.get('state')
        artist.phone = request.form.get('phone')
        artist.image_link = request.form.get('image_link')
        artist.facebook_link = request.form.get('facebook_link')
        artist.website_link = request.form.get('website_link')
        artist.looking_for_venue = check
        artist.description = request.form.get('seeking_description')
        artist.genres = request.form.getlist('genres')
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if not error:
        flash('artist ' + request.form['name'] + ' was successfully updated!')
    else:
        flash('artist ' + request.form['name'] +
              ' was not  edited!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    error = False
    try:
        venue = Venue.query.get(venue_id)
        print("venue", venue.name)
        check = False
        if request.form.get('seeking_talent') == 'y':
            check = True
        venue.name = request.form.get('name')
        venue.city = request.form.get('city')
        venue.state = request.form.get('state')
        venue.phone = request.form.get('phone')
        venue.image_link = request.form.get('image_link')
        venue.facebook_link = request.form.get('facebook_link')
        venue.website_link = request.form.get('website_link')
        venue.looking_for_venue = check
        venue.description = request.form.get('seeking_description')
        venue.genres = request.form.getlist('genres')
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    else:
        flash('Venue ' + request.form['name'] +
              ' was not  updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    form = ArtistForm()
    try:
        check = False
        if request.form.get('seeking_venue') == 'y':
            check = True
        artist = Artist(
            name=request.form.get('name'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            phone=request.form.get('phone'),
            image_link=request.form.get('image_link'),
            facebook_link=request.form.get('facebook_link'),
            website_link=request.form.get('website_link'),
            looking_for_venue=check,
            description=request.form.get('seeking_description'),
            genres=request.form.getlist('genres')
        )
        db.session.add(artist)
        db.session.commit()
        print(request.form.get('seeking_venue'))
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        flash('Artist was ' + request.form['name'] + ' successfully listed!')

    else:
        flash('An error occurred. Artist ' +
              request.form["name"] + ' could not be listed.')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    all = db.session.query(Shows, Venue, Artist).join(Artist
                                                      ).filter(Venue.id == Shows.venue_id, Artist.id == Shows.artist_id).all()

    return render_template('pages/shows.html', shows=all)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    error = False
    try:
        show = Shows(
            venue_id=request.form.get("venue_id"),
            artist_id=request.form.get("artist_id"),
            start_time=request.form.get("start_time")
        )
        db.session.add(show)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        flash('Show was successfully listed!')
    else:
        flash('An error occurred. Show could not be listed.')
    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
