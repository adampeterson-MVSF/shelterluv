import PropTypes from 'prop-types';

/**
 * Header error message display component
 */
export function HeaderError({ message }) {
  return <div className="error-message">{message}</div>;
}

HeaderError.propTypes = {
  message: PropTypes.string.isRequired
};
