import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
from flask import abort, render_template, Flask
import logging
import sqlite3
import re

APP = Flask(__name__)

global DB
DB = dict()

def connect():
  global DB
  c = sqlite3.connect('Billionaires.db', check_same_thread=False)
  c.row_factory = sqlite3.Row
  DB['conn'] = c
  DB['cursor'] = c.cursor()
  logging.info('Connected to database')

def execute(sql,args=None):
  global DB
  sql = re.sub('\s+',' ', sql)
  logging.info('SQL: {} Args: {}'.format(sql,args))
  if args:
    return DB['cursor'].execute(sql, args)
  return DB['cursor'].execute(sql)

def close():
  global DB
  DB['conn'].close()

connect()

# Start page
@APP.route('/')
def index():
    stats = {}
    stats = execute('''
    SELECT * FROM
      (SELECT COUNT(*) n_Billionaires FROM Billionaires)
    JOIN
      (SELECT COUNT(*) n_Countries FROM Countries)
    JOIN
      (SELECT COUNT(*) n_Cities FROM Cities)
    JOIN 
      (SELECT COUNT(*) n_States FROM States)
    JOIN 
      (SELECT COUNT(*) n_Regions FROM Regions)
    JOIN 
      (SELECT COUNT(*) n_Continents FROM Continents)
    JOIN 
      (SELECT COUNT(*) n_Companies FROM Companies)
    JOIN 
      (SELECT COUNT(*) n_Billionaire_Companies FROM Billionaire_Companies)
    ''').fetchone()
    logging.info(stats)
    return render_template('index.html',stats=stats)

# Billionaires
@APP.route('/billionaires/')
def list_billionaires():
    global DB
    billionaires = execute(
      '''
      SELECT b.billionaire_id, b.fullname, b.age, b.wealth, b.city_id, b.country_id, c.company_id 
      FROM Billionaires b
      JOIN Billionaire_Companies bc on b.billionaire_id = bc.billionaire_id
      JOIN Companies c on c.company_id = bc.company_id
      ORDER BY b.billionaire_id
      ''')
    
    columns = [desc[0] for desc in DB['cursor'].description]
    rows = [dict(zip(columns, row)) for row in DB['cursor'].fetchall()]
    
    return render_template('doEverything-list.html', columns=columns, rows=rows)


@APP.route('/billionaires/<int:id>/')
def get_billionaire(id):
  billionaire = execute(
      '''
      SELECT b.billionaire_id, b.firstname, b.lastname, b.fullname, b.age, b.gender, b.birth_date, b.birth_day, b.birth_month, b.birth_year, b.position, b.wealth, b.city_id, c.city_of_residence, b.country_id, c1.country_of_residence, com.company_id, com.resource, com.industry
      FROM Billionaires b
      JOIN Cities c on b.city_id = c.city_id
      JOIN Countries c1 on b.country_id = c1.country_id
      JOIN Billionaire_Companies bc on bc.billionaire_id = b.billionaire_id
      JOIN Companies com on com.company_id = bc.company_id
      WHERE b.billionaire_id = ? 
      ''', [id]).fetchone()

  if billionaire is None:
     abort(404, 'Billionaire_id {} does not exist.'.format(id))
  
  return render_template('billionaire.html', 
           billionaire=billionaire)

@APP.route('/billionaires/search/<expr>/')
def search_billionaire(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  billionaires = execute(
      ''' 
      SELECT billionaire_id, fullname
      FROM Billionaires 
      WHERE fullname LIKE ?
      ''', [expr]).fetchall()
  
  return render_template('billionaire-search.html',
           search=search,billionaires=billionaires)

# Companies
@APP.route('/companies/')
def list_companies():
    global DB
    companies = execute('''
      SELECT company_id, resource, industry 
      FROM Companies
      ORDER BY company_id
    ''')

    columns = [desc[0] for desc in DB['cursor'].description]
    rows = [dict(zip(columns, row)) for row in DB['cursor'].fetchall()]

    return render_template('doEverything-list.html', columns=columns, rows=rows)


@APP.route('/companies/<int:id>/')
def view_company_details(id):
  company = execute(
    '''
    SELECT company_id, resource, industry
    FROM Companies 
    WHERE company_id = ?
    ''', [id]).fetchone()

  if company is None:
     abort(404, 'Company_id {} does not exist.'.format(id))

  billionaire_companies = execute(
    '''
    SELECT bc.billionaire_id, b.fullname
    FROM Billionaire_Companies bc
    JOIN Billionaires b on b.billionaire_id = bc.billionaire_id
    WHERE bc.company_id = ?
    ORDER BY b.fullname
    ''', [id]).fetchall()

  return render_template('company.html', 
           company=company, billionaire_companies=billionaire_companies)
 
@APP.route('/companies/search/<expr>/')
def search_companies(expr):
  # SQL INJECTION POSSIBLE! - avoid this!
  search = { 'expr': expr }
  expr = '%' + expr + '%'

  companies = execute(
      ''' 
      SELECT company_id, resource
      FROM Companies
      WHERE resource LIKE ?
      ''', [expr]).fetchall()
  
  return render_template('company-search.html', 
           search=search,companies=companies)

# Countries
@APP.route('/countries/')
def list_countries():
    global DB
    countries = execute('''
      SELECT country_id, country_of_residence, continent_id  
      FROM Countries
      ORDER BY country_id
    ''')

    columns = [desc[0] for desc in DB['cursor'].description]
    rows = [dict(zip(columns, row)) for row in DB['cursor'].fetchall()]

    return render_template('doEverything-list.html', columns=columns, rows=rows)

@APP.route('/countries/<int:id>/')
def view_country_details(id):
  country = execute(
    '''
    SELECT c.country_id, c.country_of_residence, c.continent_id, c.country_latitude, c.country_longitude, c.country_pop, c.life_exp, c.cpi_country, c.cpi_change, c.gdp_country, c.g_primary, c.g_tertiary, c.tax_revenue, c.tax_rate, c2.continent
    FROM Countries c
    JOIN Cities c1 on c1.country_id = c.country_id
    JOIN Continents c2 on c2.continent_id = c.continent_id
    WHERE c.country_id = ?
    ''', [id]).fetchone()

  if country is None:
     abort(404, 'Country_id {} does not exist.'.format(id))

  country_city = execute(
     '''
    SELECT c1.city_id, c1.city_of_residence
    FROM Cities c1
    JOIN Countries c on c.country_id = c1.country_id
    WHERE c1.country_id = ? 
    ''', [id]).fetchall()

  return render_template('country.html', 
           country=country, country_city=country_city)

@APP.route('/countries/search/<expr>/')
def search_countries(expr):
  # SQL INJECTION POSSIBLE! - avoid this!
  search = { 'expr': expr }
  expr = '%' + expr + '%'

  countries = execute(
      ''' 
      SELECT country_id, country_of_residence
      FROM Countries
      WHERE country_of_residence LIKE ?
      ''', [expr]).fetchall()
  
  return render_template('country-search.html', 
           search=search,countries=countries)

# Cities
@APP.route('/cities/')
def list_cities():
    global DB
    countries = execute('''
      SELECT city_id, city_of_residence, state_id, country_id  
      FROM Cities
      ORDER BY city_id
    ''')

    columns = [desc[0] for desc in DB['cursor'].description]
    rows = [dict(zip(columns, row)) for row in DB['cursor'].fetchall()]

    return render_template('doEverything-list.html', columns=columns, rows=rows)

@APP.route('/cities/<int:id>/')
def view_city_details(id):
  city = execute(
    '''
    SELECT c.city_id, c.city_of_residence, r.region_id, c.state_id, c.country_id, c1.country_of_residence, r.res_region, s.res_state
    FROM Cities c
    JOIN Countries c1 on c1.country_id = c.country_id
    JOIN States s on s.state_id = c.state_id
    JOIN Regions r on s.region_id = r.region_id
    WHERE c.city_id = ?
    ''', [id]).fetchone()

  if city is None:
     abort(404, 'City_id {} does not exist.'.format(id))

  billionaires_city = execute(
     '''
    SELECT b.billionaire_id, b.fullname
    FROM Billionaires b
    JOIN Cities c on b.city_id = c.city_id
    WHERE c.city_id = ? 
    ''', [id]).fetchall()
  
  return render_template('city.html', 
           city=city, billionaires_city=billionaires_city)

@APP.route('/cities/search/<expr>/')
def search_cities(expr):
  # SQL INJECTION POSSIBLE! - avoid this!
  search = { 'expr': expr }
  expr = '%' + expr + '%'

  cities = execute(
      ''' 
      SELECT city_id, city_of_residence
      FROM Cities
      WHERE city_of_residence LIKE ?
      ''', [expr]).fetchall()
  
  return render_template('city-search.html', 
           search=search,cities=cities)

# States
@APP.route('/states/')
def list_states():
    global DB
    countries = execute('''
      SELECT s.state_id, s.res_state
      FROM States s
      ORDER BY s.state_id
    ''')

    columns = [desc[0] for desc in DB['cursor'].description]
    rows = [dict(zip(columns, row)) for row in DB['cursor'].fetchall()]

    return render_template('doEverything-list.html', columns=columns, rows=rows)

@APP.route('/states/<int:id>/')
def view_state_details(id):
  state = execute(
    '''
    SELECT s.state_id, s.res_state, r.res_region, c1.country_id, c1.country_of_residence
    FROM States s
    JOIN Cities c on c.state_id = s.state_id
    JOIN Regions r on r.region_id = s.region_id
    JOIN Countries c1 on c1.country_id = c.country_id
    WHERE s.state_id = ?
    ''', [id]).fetchone()

  if state is None:
     abort(404, 'State_id {} does not exist.'.format(id))

  state_city = execute(
     '''
    SELECT s.state_id, s.res_state, c.city_id, c.city_of_residence
    FROM States s
    JOIN Cities c on c.state_id = s.state_id
    WHERE s.state_id = ? 
    ''', [id]).fetchall()
  
  return render_template('state.html', 
           state=state, state_city=state_city)

@APP.route('/states/search/<expr>/')
def search_state(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  states = execute(
      ''' 
      SELECT state_id, res_state
      FROM States 
      WHERE res_state LIKE ?
      ''', [expr]).fetchall()
  
  return render_template('state-search.html',
           search=search,states=states)

if __name__ == '__main__':
    APP.run(debug=True)
