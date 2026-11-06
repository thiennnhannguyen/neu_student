import { Search } from 'lucide-react';
import Input from './Input';

export default function SearchBox(props) {
  return (
    <span className="search-box">
      <Search size={16} aria-hidden="true" />
      <Input type="search" {...props} />
    </span>
  );
}
