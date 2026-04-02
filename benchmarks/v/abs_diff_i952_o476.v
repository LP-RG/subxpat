module abs_diff_i952_o476(a,b,r);
input [475:0] a,b;
output [475:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
