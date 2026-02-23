module abs_diff_i432_o216(a,b,r);
input [215:0] a,b;
output [215:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
