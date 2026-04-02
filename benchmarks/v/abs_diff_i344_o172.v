module abs_diff_i344_o172(a,b,r);
input [171:0] a,b;
output [171:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
