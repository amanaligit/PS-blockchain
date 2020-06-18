# module 2-creating a cryptocurrency
# we need requests library ver 2.18.4

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from base64 import b64encode


# bluilding a blockchain
class BlockChain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(mined_block=self.proof_of_work(0, "origin"))
        self.nodes = set()

    def create_block(self, mined_block):
        self.transactions = []
        self.chain.append(mined_block)

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_hash, type):
        check_proof = False
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'nonce': 1,
                 'type':type,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions
                 }
        while check_proof is False:
            hash_operation = hashlib.sha256(json.dumps(
                block, sort_keys=True).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                block['nonce'] += 1
        return block

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            hash_operation = hashlib.sha256(json.dumps(
                block, sort_keys=True).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_payment(self, sender, receiver):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount,
                                  })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_design(self,filename, name):
        self.transactions.append({'filename': filename,
                                'name': name
                                })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_inventory(self, productinfo, location, status, volume):
        self.transactions.append({'productinfo': productinfo,
                                'location': location,
                                'status': status,
                                "volume": volume
                                })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1


    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_curr_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False


# Mining our Blockchain

# creating a web app
app = Flask(__name__)

node_address = str(uuid4()).replace('-', '')

# creating a blockchain
blockchain = BlockChain()


# mining a block
@app.route('/mine_inventory', methods=['GET'])
def mine_inventory():
    blockchain.replace_chain()
    #network = blockchain.nodes
    # for node in network:
    # blockchain.transactions = blockchain.transactions + (requests.get(f'http://{node}/get_trans')).json()[
    # 'transactions']

    previous_block = blockchain.get_previous_block()
    previous_hash = blockchain.hash(previous_block)

    #blockchain.add_payment(sender=node_address, receiver='Aman', amount=1)
    mined_block = blockchain.proof_of_work(previous_hash, "inventory")
    blockchain.create_block(mined_block)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': mined_block['index'],
                'timestamp': mined_block['timestamp'],
                'nonce': mined_block['nonce'],
                'type': mined_block['type'],
                'previous_hash': mined_block['previous_hash'],
                'transactions': mined_block['transactions'],
                'hash': blockchain.hash(mined_block)}

    return render_template("mined.html", response=response)

@app.route('/mine_design', methods=['GET'])
def mine_design():
    blockchain.replace_chain()
    previous_block = blockchain.get_previous_block()
    previous_hash = blockchain.hash(previous_block)
    mined_block = blockchain.proof_of_work(previous_hash, "design")
    blockchain.create_block(mined_block)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': mined_block['index'],
                'timestamp': mined_block['timestamp'],
                'nonce': mined_block['nonce'],
                'type': mined_block['type'],
                'previous_hash': mined_block['previous_hash'],
                'transactions': mined_block['transactions'],
                'hash': blockchain.hash(mined_block)}

    return render_template("mined.html", response=response)

# getting the full BlockChain
@app.route("/", methods=["GET"])
def index():
    nodes= ["http://127.0.0.1:5001",
            "http://127.0.0.1:5002",
            "http://127.0.0.1:5003",
            "http://127.0.0.1:5004"]

    for node in nodes:
        blockchain.add_node(node)
    # render_template("payments.html", message="Please enter Payments detail to continue")
    # render_template("inventory.html", message="Please enter Payments detail to continue")
    return render_template("design.html", message="Please upload the design image to continue")

# introductory page
#################################


@app.route('/get_trans', methods=['GET'])
def get_trans():
    response = {'transactions': blockchain.transactions}
    blockchain.transactions = []
    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    blockchain.replace_chain()

    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return render_template("blockchain.html", response=response)


@app.route('/get_curr_chain', methods=['GET'])
def get_curr_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid is True:
        response = {'message': 'chain is valid!'}
    else:
        response = {'message': 'chain is not valid!'}

    return jsonify(response), 200


# Adding a new transaction to the Blockchain
@app.route('/add_payment', methods=['POST'])
def add_payment():
    sender = request.form.get("sender")
    receiver = request.form.get("receiver")
    amount = request.form.get("amount")
    try:
        amount = int(amount)
    except ValueError:
        return render_template("error.html", message="Please enter a valid amount")
    if sender == "" or receiver == "":
        return render_template("error.html", message="Please enter Sender or Reciever")
    index = blockchain.add_payment(
        sender, receiver, amount, 'unapplicable', 'unapplicable', 'unapplicable', 'unapplicable')
    response = f'This transaction will be added to block {index}'
    return render_template("payments.html", message=response)


@app.route('/upload_design', methods=['POST'])
def upload_design():
    if request.files:
        image = request.files['design']
        name = request.form.get("name")
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static/", image.filename)
        image.save(path)
        index = blockchain.add_design(image.filename, name)


    response = f'This design will be added to block {index}'
    return render_template("design.html", message=response)
# adding inventory information


@app.route('/manage_inventory', methods=['POST'])
def manage_inventory():
    productinfo = request.form.get("productinfo")
    location = request.form.get("location")
    volume = request.form.get("volume")
    status = request.form['status']

    try:
        volume = int(volume)
    except ValueError:
        return render_template("error.html", message="Please enter a valid quantity")
    if productinfo == "" or location == "":
        return render_template("error.html", message="Please fill all the fields")
    index = blockchain.add_inventory(productinfo, location, status, volume)
    response = f'This information will be added to block {index}'
    return render_template("inventory.html", message=response)

# viewing block information


@app.route("/<int:index>", methods=["GET"])
def get_block(index):
    block = blockchain.chain[index-1]
    if (block['type']=="origin"):
        return render_template("block_origin.html", block=block, hash=blockchain.hash(block))
    elif (block['type']=="inventory"):
        return render_template("block_inventory.html", block=block, hash=blockchain.hash(block))
    elif (block['type']=="payment"):
        return render_template("block_payment.html", block=block, hash=blockchain.hash(block))
    elif (block['type']=="design"):
        return render_template("block_design.html", block=block, hash=blockchain.hash(block))
    elif (block['type']=="manufacturing"):
        return render_template("block_manu.html", block=block, hash=blockchain.hash(block))



# Decentralizing our cryptocurrency


# connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No nodes!", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {
        "message": "All the nodes are now connected, The zcoin blockchain contains the following number of nodes:",
        "total_nodes": list(blockchain.nodes)}
    return jsonify(response), 201


@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced is True:
        response = {'message': 'chain was replaced with the longest chain!',
                    'newchain': blockchain.chain}
    else:
        response = {'message': 'chain is upto date!',
                    'newchain': blockchain.chain}

    return jsonify(response), 200


app.run(host='0.0.0.0', port=5003, debug=True)
