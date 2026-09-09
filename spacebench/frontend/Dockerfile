# Angular build
FROM node:22.16 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build -- --configuration=development  --prerender=false


# MkDocs
#RUN source .venv/bin/activate
#RUN mkdocs build --clean
#COPY docs/site/ /usr/local/apache2/htdocs/docs/
FROM python:3.12 AS mkdocs-builder
WORKDIR /docs
# copy only the docs folder to keep build small
COPY docs/ .
RUN pip install mkdocs-material mkdocs-static-i18n
RUN mkdocs build --clean

# Apache for static serving
FROM httpd:latest
COPY --from=builder /app/dist/frontend/browser /usr/local/apache2/htdocs
COPY --from=mkdocs-builder /docs/site /usr/local/apache2/htdocs/docs
COPY --from=mkdocs-builder /docs/img/ /usr/local/apache2/htdocs/docs/assets/images

# Copy .htaccess rewrite rules for Angular routing
RUN echo 'RewriteEngine On' > /usr/local/apache2/htdocs/.htaccess && \
    echo '' >> /usr/local/apache2/htdocs/.htaccess && \
    echo 'RewriteCond %{REQUEST_URI} ^/assets/' >> /usr/local/apache2/htdocs/.htaccess && \
    echo 'RewriteRule ^ - [L]' >> /usr/local/apache2/htdocs/.htaccess && \
    echo '' >> /usr/local/apache2/htdocs/.htaccess && \
    echo 'RewriteCond %{REQUEST_FILENAME} !-f' >> /usr/local/apache2/htdocs/.htaccess && \
    echo 'RewriteCond %{REQUEST_FILENAME} !-d' >> /usr/local/apache2/htdocs/.htaccess && \
    echo 'RewriteRule ^ index.html [L]' >> /usr/local/apache2/htdocs/.htaccess


# Enable mod_rewrite and allow .htaccess overrides
RUN sed -i 's/#LoadModule rewrite_module/LoadModule rewrite_module/' /usr/local/apache2/conf/httpd.conf && \
    sed -i 's/AllowOverride None/AllowOverride All/' /usr/local/apache2/conf/httpd.conf

RUN if [ -f /usr/local/apache2/htdocs/index.csr.html ]; then \
      mv /usr/local/apache2/htdocs/index.csr.html /usr/local/apache2/htdocs/index.html; \
    fi

RUN echo "AddType application/javascript .js" >> /usr/local/apache2/conf/httpd.conf && \
    echo "AddType text/css .css" >> /usr/local/apache2/conf/httpd.conf

