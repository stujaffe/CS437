Place the Amazon root certificate .pem file in this folder (found here: https://www.amazontrust.com/repository/AmazonRootCA1.pem)
I separated the Aamazon root certificate from the other certificate files for thing IoT things in case we want to delete the
things and need to mass delete the certificates in for the things, we don't want to delete the Amazon root certificate.