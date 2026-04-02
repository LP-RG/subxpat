module abs_diff_i712_o356(a,b,r);
input [355:0] a,b;
output [355:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
