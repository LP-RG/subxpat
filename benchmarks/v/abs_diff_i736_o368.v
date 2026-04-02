module abs_diff_i736_o368(a,b,r);
input [367:0] a,b;
output [367:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
