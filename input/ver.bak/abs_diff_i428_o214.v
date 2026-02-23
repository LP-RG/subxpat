module abs_diff_i428_o214(a,b,r);
input [213:0] a,b;
output [213:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
