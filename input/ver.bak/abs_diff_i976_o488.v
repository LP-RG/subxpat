module abs_diff_i976_o488(a,b,r);
input [487:0] a,b;
output [487:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
