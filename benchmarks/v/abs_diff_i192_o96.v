module abs_diff_i192_o96(a,b,r);
input [95:0] a,b;
output [95:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
