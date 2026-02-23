module abs_diff_i220_o110(a,b,r);
input [109:0] a,b;
output [109:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
