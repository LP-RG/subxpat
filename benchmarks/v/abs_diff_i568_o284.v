module abs_diff_i568_o284(a,b,r);
input [283:0] a,b;
output [283:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
